from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from app.services.weekend_scanner import WeekendScanner
from app.services.daily_scanner import DailyScanner
from app.services.pattern_recognizer import PatternRecognizer
from app.database import AsyncSessionLocal
from app.utils.redis_client import get_redis
from app.utils.helpers import is_trading_day

logger = logging.getLogger(__name__)

class SignalGenerator:
    """信号生成器 - 整合所有扫描和识别服务"""

    def __init__(self):
        pass

    async def generate_weekend_signals(self) -> Dict:
        """生成周末扫描信号"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()

            scanner = WeekendScanner(db, redis)
            result = await scanner.scan_all_stocks()

            return result

    async def generate_daily_signals(self) -> Dict:
        """生成日筛选信号"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()

            # 1. 获取最新的周末扫描结果
            weekend_scanner = WeekendScanner(db, redis)
            weekend_results = await weekend_scanner.get_latest_results()

            if not weekend_results or not weekend_results.get('results'):
                logger.warning("No weekend scan results found for daily scan")
                return {
                    'scan_date': datetime.now().date(),
                    'pool_count': 0,
                    'results': [],
                    'signals': []
                }

            # 2. 执行日筛选
            daily_scanner = DailyScanner(db, redis)
            pool_result = await daily_scanner.scan_daily_pool(weekend_results['results'])

            # 3. 形态识别
            recognizer = PatternRecognizer(db, redis)
            signals = await recognizer.recognize_buy_signals(pool_result['results'])

            return {
                'scan_date': pool_result['scan_date'],
                'pool_count': pool_result['pool_count'],
                'results': pool_result['results'],
                'signals': signals,
                'signal_count': len(signals)
            }

    async def update_realtime_data(self):
        """更新实时数据"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()

            # 更新120分钟MACD数据
            daily_scanner = DailyScanner(db, redis)
            await daily_scanner.update_120min_macd()

    async def get_today_signals(self, status: str = 'PENDING') -> Optional[Dict]:
        """获取今日信号"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()
            recognizer = PatternRecognizer(db, redis)
            return await recognizer.get_latest_signals(status)

    async def confirm_signal(self, signal_id: int, note: str = None) -> bool:
        """确认信号"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()
            recognizer = PatternRecognizer(db, redis)
            return await recognizer.update_signal_status(signal_id, 'CONFIRMED', note)

    async def invalidate_signal(self, signal_id: int, reason: str) -> bool:
        """作废信号"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()
            recognizer = PatternRecognizer(db, redis)
            return await recognizer.update_signal_status(signal_id, 'INVALID', reason)

    async def get_signal_history(self, days: int = 30) -> List[Dict]:
        """获取信号历史"""
        async with AsyncSessionLocal() as db:
            redis = await get_redis()

            # 获取最近N天的信号
            start_date = datetime.now().date() - timedelta(days=days)

            from app.models.signal import TradeSignal
            from sqlalchemy import select, and_

            stmt = select(TradeSignal).where(
                and_(
                    TradeSignal.signal_date >= start_date,
                    TradeSignal.signal_type == 'BUY'
                )
            ).order_by(TradeSignal.signal_date.desc(), TradeSignal.id.desc())

            result = await db.execute(stmt)
            signals = result.scalars().all()

            return [
                {
                    'id': s.id,
                    'code': s.stock_code,
                    'name': s.stock_name,
                    'signal_date': s.signal_date,
                    'signal_price': float(s.signal_price),
                    'status': s.status,
                    'reason': s.reason,
                    'created_at': s.created_at
                }
                for s in signals
            ]

    async def get_stock_signal_summary(self, stock_code: str) -> Dict:
        """获取个股信号汇总"""
        async with AsyncSessionLocal() as db:
            from app.models.signal import TradeSignal
            from sqlalchemy import select, func, and_

            # 获取信号统计
            stmt = select(
                TradeSignal.signal_type,
                TradeSignal.status,
                func.count(TradeSignal.id).label('count')
            ).where(
                TradeSignal.stock_code == stock_code
            ).group_by(
                TradeSignal.signal_type,
                TradeSignal.status
            )

            result = await db.execute(stmt)
            stats = result.all()

            # 获取最新信号
            stmt = select(TradeSignal).where(
                TradeSignal.stock_code == stock_code
            ).order_by(TradeSignal.signal_date.desc()).limit(1)

            result = await db.execute(stmt)
            latest_signal = result.scalar_one_or_none()

            return {
                'code': stock_code,
                'signal_stats': [
                    {
                        'type': s.signal_type,
                        'status': s.status,
                        'count': s.count
                    }
                    for s in stats
                ],
                'latest_signal': {
                    'date': latest_signal.signal_date,
                    'type': latest_signal.signal_type,
                    'price': float(latest_signal.signal_price),
                    'status': latest_signal.status
                } if latest_signal else None
            }

    async def should_run_weekend_scan(self) -> bool:
        """判断是否应该运行周末扫描"""
        today = datetime.now().date()

        # 只在周日运行
        if today.weekday() != 6:  # 0=周一, 6=周日
            return False

        # 检查是否已经运行过
        async with AsyncSessionLocal() as db:
            from app.models.scan_result import WeekendScanResult
            from sqlalchemy import select, func

            stmt = select(func.count(WeekendScanResult.id)).where(
                WeekendScanResult.scan_date == today
            )

            result = await db.execute(stmt)
            count = result.scalar()

            return count == 0

    async def should_run_daily_scan(self) -> bool:
        """判断是否应该运行日筛选"""
        now = datetime.now()
        today = now.date()

        # 检查是否为交易日
        if not is_trading_day(today):
            return False

        # 检查时间（15:05之后）
        if now.hour < 15 or (now.hour == 15 and now.minute < 5):
            return False

        # 检查是否已经运行过
        async with AsyncSessionLocal() as db:
            from app.models.scan_result import DailyPool
            from sqlalchemy import select, func

            stmt = select(func.count(DailyPool.id)).where(
                DailyPool.scan_date == today
            )

            result = await db.execute(stmt)
            count = result.scalar()

            return count == 0