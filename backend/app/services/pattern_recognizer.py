import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import asyncio
import logging

from app.models.stock import Stock, DailyKline, LimitUpRecord
from app.models.scan_result import DailyPool
from app.models.signal import TradeSignal
from app.utils.indicators import calculate_price_change, calculate_upper_shadow
from app.utils.helpers import is_limit_up
from app.utils.redis_client import get_cache, set_cache
from app.config import settings

logger = logging.getLogger(__name__)

class PatternRecognizer:
    """交易形态识别器"""

    def __init__(self, db_session: AsyncSession, redis_client):
        self.db = db_session
        self.redis = redis_client

    async def recognize_buy_signals(self, daily_pool: List[Dict]) -> List[Dict]:
        """
        识别买入信号: 缩量旗形 + 放量中阳

        步骤:
        1. 找到最近一次涨停板
        2. 检查涨停后2-8天回调期间是否缩量
        3. 检查今天是否放量中阳
        """
        logger.info(f"Recognizing buy signals for {len(daily_pool)} stocks...")
        start_time = datetime.now()

        signals = []

        # 异步处理每只股票
        tasks = []
        for stock in daily_pool:
            task = asyncio.create_task(self._process_buy_signal(stock))
            tasks.append(task)

            # 限制并发数量
            if len(tasks) >= 10:
                completed = await asyncio.gather(*tasks[:10])
                for signal in completed:
                    if signal:
                        signals.append(signal)
                tasks = tasks[10:]

        # 处理剩余任务
        if tasks:
            completed = await asyncio.gather(*tasks)
            for signal in completed:
                if signal:
                    signals.append(signal)

        # 保存信号到数据库
        await self._save_signals(signals)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Pattern recognition completed in {duration:.2f} seconds")
        logger.info(f"Generated {len(signals)} buy signals")

        return signals

    async def _process_buy_signal(self, stock: Dict) -> Optional[Dict]:
        """处理单只股票的买入信号"""
        code = stock['code']
        name = stock['name']

        try:
            # 1. 查找最近涨停板
            limit_up_info = await self._find_recent_limit_up(code)
            if not limit_up_info:
                return None

            # 2. 检查缩量旗形
            if not await self._check_shrinking_flag(code, limit_up_info):
                return None

            # 3. 检查今日放量中阳
            breakout_info = await self._check_breakout_candle(code)
            if not breakout_info:
                return None

            # 4. 计算止损位
            stop_loss = self._calculate_stop_loss(limit_up_info)

            # 生成信号
            signal = {
                'code': code,
                'name': name,
                'signal_type': 'BUY',
                'signal_price': breakout_info['close'],
                'limit_up_date': limit_up_info['date'],
                'pullback_days': breakout_info['pullback_days'],
                'volume_ratio': breakout_info['volume_ratio'],
                'price_change': breakout_info['price_change'],
                'upper_shadow': breakout_info['upper_shadow'],
                'stop_loss_price': stop_loss,
                'stop_loss_reason': "涨停板中枢",
                'reason': self._generate_reason(breakout_info)
            }

            return signal

        except Exception as e:
            logger.error(f"Error processing buy signal for {code}: {e}")
            return None

    async def _find_recent_limit_up(self, stock_code: str, days: int = 30) -> Optional[Dict]:
        """查找最近一次涨停板"""
        try:
            # 获取最近N天的日线数据
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            stmt = select(DailyKline).where(
                and_(
                    DailyKline.stock_code == stock_code,
                    DailyKline.trade_date >= start_date,
                    DailyKline.trade_date <= end_date
                )
            ).order_by(DailyKline.trade_date.desc())

            result = await self.db.execute(stmt)
            klines = result.scalars().all()

            if len(klines) < 2:
                return None

            # 创建DataFrame
            df = pd.DataFrame([{
                'date': k.trade_date,
                'open': float(k.open),
                'close': float(k.close),
                'volume': k.volume
            } for k in reversed(klines)])

            # 查找涨停板
            for i in range(len(df)):
                if i == 0:  # 跳过第一天（需要前一天收盘价）
                    continue

                row = df.iloc[i]
                prev_close = df.iloc[i-1]['close']

                # 涨停判断
                if is_limit_up(row['open'], row['close'], prev_close, settings.limit_up_threshold):
                    return {
                        'date': row['date'],
                        'price': row['close'],
                        'volume': row['volume'],
                        'index': i
                    }

            return None

        except Exception as e:
            logger.error(f"Error finding recent limit up for {stock_code}: {e}")
            return None

    async def _check_shrinking_flag(self, stock_code: str, limit_up_info: Dict) -> bool:
        """检查涨停后是否形成缩量旗形"""
        try:
            # 获取涨停后的K线（最多8天）
            limit_date = limit_up_info['date']
            end_date = limit_date + timedelta(days=10)  # 多取一些数据

            stmt = select(DailyKline).where(
                and_(
                    DailyKline.stock_code == stock_code,
                    DailyKline.trade_date > limit_date,
                    DailyKline.trade_date <= end_date
                )
            ).order_by(DailyKline.trade_date.asc())

            result = await self.db.execute(stmt)
            klines = result.scalars().all()

            if len(klines) < 2:
                return False

            # 创建DataFrame
            df = pd.DataFrame([{
                'date': k.trade_date,
                'volume': k.volume
            } for k in klines])

            # 只取前8天
            pullback = df.head(8)

            if len(pullback) < 2:
                return False

            # 检查量能是否缩减
            volumes = pullback['volume'].values

            # 计算平均量能下降趋势
            mid_point = len(volumes) // 2
            avg_first_half = volumes[:mid_point].mean()
            avg_second_half = volumes[mid_point:].mean()

            # 后半段量能应小于前半段（缩量）
            if avg_second_half < avg_first_half * 0.7:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking shrinking flag for {stock_code}: {e}")
            return False

    async def _check_breakout_candle(self, stock_code: str) -> Optional[Dict]:
        """检查今日是否为放量中阳"""
        try:
            # 获取最近2天的数据
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=5)

            stmt = select(DailyKline).where(
                and_(
                    DailyKline.stock_code == stock_code,
                    DailyKline.trade_date >= start_date,
                    DailyKline.trade_date <= end_date
                )
            ).order_by(DailyKline.trade_date.asc())

            result = await self.db.execute(stmt)
            klines = result.scalars().all()

            if len(klines) < 2:
                return None

            # 获取最后两天的数据
            today = klines[-1]
            yesterday = klines[-2]

            # 放量检查
            volume_ratio = today.volume / yesterday.volume if yesterday.volume > 0 else 0
            if volume_ratio < settings.breakout_volume_ratio:
                return None

            # 涨幅检查
            price_change = (today.close - yesterday.close) / yesterday.close
            if not (settings.breakout_price_change_min <= price_change <= settings.breakout_price_change_max):
                return None

            # 上影线检查
            upper_shadow = calculate_upper_shadow(today.open, today.high, today.close)
            if upper_shadow >= settings.upper_shadow_threshold:
                return None

            # 计算回调天数
            limit_up_info = await self._find_recent_limit_up(stock_code)
            if limit_up_info:
                pullback_days = (today.trade_date - limit_up_info['date']).days
            else:
                pullback_days = 0

            return {
                'close': float(today.close),
                'volume_ratio': round(volume_ratio, 2),
                'price_change': round(price_change * 100, 2),
                'upper_shadow': round(upper_shadow * 100, 2),
                'pullback_days': pullback_days
            }

        except Exception as e:
            logger.error(f"Error checking breakout candle for {stock_code}: {e}")
            return None

    def _calculate_stop_loss(self, limit_up_info: Dict) -> float:
        """计算止损价"""
        # 止损位 = 涨停板价格 * 0.90 (大约-10%)
        return round(limit_up_info['price'] * settings.stop_loss_ratio, 2)

    def _generate_reason(self, breakout_info: Dict) -> str:
        """生成买入理由"""
        return (
            f"涨停板后回调{breakout_info['pullback_days']}天形成缩量旗形，"
            f"今日放量{breakout_info['volume_ratio']}倍，"
            f"收涨{breakout_info['price_change']}%的中阳线，"
            f"上影线仅{breakout_info['upper_shadow']}%，"
            f"建议尾盘或次日早盘买入"
        )

    async def _save_signals(self, signals: List[Dict]):
        """保存信号到数据库"""
        if not signals:
            return

        try:
            for signal in signals:
                # 检查是否已存在
                stmt = select(TradeSignal).where(
                    and_(
                        TradeSignal.stock_code == signal['code'],
                        TradeSignal.signal_date == datetime.now().date(),
                        TradeSignal.signal_type == 'BUY'
                    )
                )
                result = await self.db.execute(stmt)
                if result.scalar_one_or_none():
                    continue

                # 创建新信号
                trade_signal = TradeSignal(
                    stock_code=signal['code'],
                    stock_name=signal['name'],
                    signal_type='BUY',
                    signal_date=datetime.now().date(),
                    signal_price=signal['signal_price'],
                    limit_up_date=signal['limit_up_date'],
                    pullback_days=signal['pullback_days'],
                    volume_ratio=signal['volume_ratio'],
                    price_change=signal['price_change'],
                    upper_shadow=signal['upper_shadow'],
                    stop_loss_price=signal['stop_loss_price'],
                    stop_loss_reason=signal['stop_loss_reason'],
                    reason=signal['reason'],
                    status='PENDING'
                )
                self.db.add(trade_signal)

            await self.db.commit()
            logger.info(f"Saved {len(signals)} trade signals")

        except Exception as e:
            logger.error(f"Error saving trade signals: {e}")
            await self.db.rollback()
            raise

    async def get_latest_signals(self, status: str = 'PENDING') -> Optional[Dict]:
        """获取最新的交易信号"""
        try:
            # 获取今日信号
            today = datetime.now().date()

            stmt = select(TradeSignal).where(
                and_(
                    TradeSignal.signal_date == today,
                    TradeSignal.status == status
                )
            ).order_by(TradeSignal.id.desc())

            result = await self.db.execute(stmt)
            signals = result.scalars().all()

            if not signals:
                return None

            return {
                'signal_date': today,
                'total_signals': len(signals),
                'signals': [
                    {
                        'id': s.id,
                        'code': s.stock_code,
                        'name': s.stock_name,
                        'signal_type': s.signal_type,
                        'signal_price': float(s.signal_price),
                        'limit_up_date': s.limit_up_date,
                        'pullback_days': s.pullback_days,
                        'volume_ratio': float(s.volume_ratio) if s.volume_ratio else None,
                        'price_change': float(s.price_change) if s.price_change else None,
                        'upper_shadow': float(s.upper_shadow) if s.upper_shadow else None,
                        'stop_loss_price': float(s.stop_loss_price) if s.stop_loss_price else None,
                        'stop_loss_reason': s.stop_loss_reason,
                        'status': s.status,
                        'reason': s.reason
                    }
                    for s in signals
                ]
            }

        except Exception as e:
            logger.error(f"Error getting latest signals: {e}")
            return None

    async def update_signal_status(self, signal_id: int, status: str, note: str = None) -> bool:
        """更新信号状态"""
        try:
            stmt = select(TradeSignal).where(TradeSignal.id == signal_id)
            result = await self.db.execute(stmt)
            signal = result.scalar_one_or_none()

            if not signal:
                return False

            signal.status = status
            if note:
                signal.reason = f"{signal.reason}\n更新: {note}"

            await self.db.commit()
            logger.info(f"Updated signal {signal_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            await self.db.rollback()
            return False

    async def get_signal_detail(self, signal_id: int) -> Optional[Dict]:
        """获取信号详情"""
        try:
            stmt = select(TradeSignal).where(TradeSignal.id == signal_id)
            result = await self.db.execute(stmt)
            signal = result.scalar_one_or_none()

            if not signal:
                return None

            return {
                'id': signal.id,
                'code': signal.stock_code,
                'name': signal.stock_name,
                'signal_type': signal.signal_type,
                'signal_date': signal.signal_date,
                'signal_price': float(signal.signal_price),
                'limit_up_date': signal.limit_up_date,
                'pullback_days': signal.pullback_days,
                'volume_ratio': float(signal.volume_ratio) if signal.volume_ratio else None,
                'price_change': float(signal.price_change) if signal.price_change else None,
                'upper_shadow': float(signal.upper_shadow) if signal.upper_shadow else None,
                'stop_loss_price': float(signal.stop_loss_price) if signal.stop_loss_price else None,
                'stop_loss_reason': signal.stop_loss_reason,
                'status': signal.status,
                'reason': signal.reason,
                'created_at': signal.created_at
            }

        except Exception as e:
            logger.error(f"Error getting signal detail: {e}")
            return None