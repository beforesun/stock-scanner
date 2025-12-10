import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import asyncio
import logging

from app.models.stock import Stock, DailyKline, Kline120min
from app.models.scan_result import WeekendScanResult, DailyPool
from app.utils.indicators import calculate_ma, calculate_macd, detect_golden_cross
from app.utils.redis_client import get_cache, set_cache
from app.config import settings

logger = logging.getLogger(__name__)

class DailyScanner:
    """工作日筛选器"""

    def __init__(self, db_session: AsyncSession, redis_client):
        self.db = db_session
        self.redis = redis_client
        self.vol_ma_short = settings.vol_ma_period_daily_short
        self.vol_ma_long = settings.vol_ma_period_daily_long
        self.macd_days = settings.macd_consecutive_days

    async def scan_daily_pool(self, weekend_results: List[Dict]) -> Dict:
        """
        从周末结果中筛选日线信号
        条件:
        1. 均量线20日金叉60日
        2. 120分钟MACD红柱连续放大
        """
        logger.info(f"Starting daily scan with {len(weekend_results)} weekend results...")
        start_time = datetime.now()

        results = []

        # 异步处理每只股票
        tasks = []
        for stock in weekend_results:
            task = asyncio.create_task(self._process_single_stock(stock))
            tasks.append(task)

            # 限制并发数量
            if len(tasks) >= 10:
                completed = await asyncio.gather(*tasks[:10])
                for result in completed:
                    if result:
                        results.append(result)
                tasks = tasks[10:]

        # 处理剩余任务
        if tasks:
            completed = await asyncio.gather(*tasks)
            for result in completed:
                if result:
                    results.append(result)

        # 保存结果到数据库
        await self._save_daily_pool(results)

        # 缓存结果
        await self._cache_results(results)

        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()

        logger.info(f"Daily scan completed in {scan_duration:.2f} seconds")
        logger.info(f"Total weekend stocks: {len(weekend_results)}, Daily pool count: {len(results)}")

        return {
            'scan_date': datetime.now().date(),
            'pool_count': len(results),
            'results': results,
            'duration': scan_duration
        }

    async def _process_single_stock(self, stock: Dict) -> Optional[Dict]:
        """处理单只股票"""
        code = stock['code']

        try:
            # 1. 检查均量线金叉
            golden_cross = await self._check_volume_golden_cross(code)
            if not golden_cross:
                return None

            # 2. 检查120分钟MACD
            macd_status = await self._check_120min_macd(code)
            if not macd_status:
                return None

            return {
                'code': code,
                'name': stock['name'],
                'golden_cross': True,
                'macd_120min_status': macd_status
            }

        except Exception as e:
            logger.error(f"Error processing stock {code}: {e}")
            return None

    async def _check_volume_golden_cross(self, stock_code: str) -> bool:
        """检查均量线金叉"""
        try:
            # 检查缓存
            cache_key = f"vol_golden_cross:{stock_code}:{datetime.now().strftime('%Y%m%d')}"
            cached_result = await get_cache(cache_key)
            if cached_result is not None:
                return cached_result

            # 获取日线数据
            stmt = select(DailyKline).where(
                DailyKline.stock_code == stock_code
            ).order_by(DailyKline.trade_date.desc()).limit(100)

            result = await self.db.execute(stmt)
            klines = result.scalars().all()

            if len(klines) < 70:  # 至少需要70天数据
                await set_cache(cache_key, False, ttl=3600)
                return False

            # 创建DataFrame
            df = pd.DataFrame([{
                'date': k.trade_date,
                'volume': k.volume
            } for k in reversed(klines)])

            # 计算均量线
            df['vol_ma20'] = calculate_ma(df['volume'], self.vol_ma_short)
            df['vol_ma60'] = calculate_ma(df['volume'], self.vol_ma_long)

            # 检查最近是否金叉（5天内）
            recent = df.tail(10)

            has_cross = False
            for i in range(len(recent) - 1):
                if (recent['vol_ma20'].iloc[i] <= recent['vol_ma60'].iloc[i] and
                    recent['vol_ma20'].iloc[i + 1] > recent['vol_ma60'].iloc[i + 1]):
                    has_cross = True
                    break

            # 缓存结果
            await set_cache(cache_key, has_cross, ttl=3600)
            return has_cross

        except Exception as e:
            logger.error(f"Error checking volume golden cross for {stock_code}: {e}")
            return False

    async def _check_120min_macd(self, stock_code: str) -> Optional[str]:
        """检查120分钟MACD红柱连续放大"""
        try:
            # 获取最近10天的120分钟数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)

            stmt = select(Kline120min).where(
                and_(
                    Kline120min.stock_code == stock_code,
                    Kline120min.datetime >= start_date,
                    Kline120min.datetime <= end_date
                )
            ).order_by(Kline120min.datetime.desc())

            result = await self.db.execute(stmt)
            klines = result.scalars().all()

            if len(klines) < 20:  # 至少需要20根120分钟K线
                return None

            # 创建DataFrame
            df = pd.DataFrame([{
                'datetime': k.datetime,
                'macd_hist': k.macd_hist
            } for k in reversed(klines)])

            # 检查红柱连续放大
            consecutive_count = 0
            for i in range(len(df) - 1, 0, -1):
                if (df['macd_hist'].iloc[i] > 0 and  # 红柱
                    df['macd_hist'].iloc[i] > df['macd_hist'].iloc[i-1]):  # 放大
                    consecutive_count += 1
                else:
                    break

            if consecutive_count >= self.macd_days:
                return f"红柱连续放大{consecutive_count}根"

            return None

        except Exception as e:
            logger.error(f"Error checking 120min MACD for {stock_code}: {e}")
            return None

    async def _save_daily_pool(self, results: List[Dict]):
        """保存日筛选池结果"""
        if not results:
            return

        try:
            # 先删除今天的记录
            today = datetime.now().date()
            await self.db.execute(
                DailyPool.__table__.delete().where(
                    DailyPool.scan_date == today
                )
            )

            # 插入新记录
            for result in results:
                # 获取股票的均量线数据
                stmt = select(DailyKline).where(
                    DailyKline.stock_code == result['code']
                ).order_by(DailyKline.trade_date.desc()).limit(1)

                db_result = await self.db.execute(stmt)
                latest_kline = db_result.scalar_one_or_none()

                daily_pool = DailyPool(
                    scan_date=today,
                    stock_code=result['code'],
                    stock_name=result['name'],
                    vol_ma20=latest_kline.vol_ma20 if latest_kline else None,
                    vol_ma60=latest_kline.vol_ma60 if latest_kline else None,
                    golden_cross=result['golden_cross'],
                    macd_120min_status=result['macd_120min_status']
                )
                self.db.add(daily_pool)

            await self.db.commit()
            logger.info(f"Saved {len(results)} daily pool results")

        except Exception as e:
            logger.error(f"Error saving daily pool results: {e}")
            await self.db.rollback()
            raise

    async def _cache_results(self, results: List[Dict]):
        """缓存日筛选池结果"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            cache_key = f"daily_pool:{today}"

            cache_data = {
                'scan_date': today,
                'pool_count': len(results),
                'results': results
            }

            await set_cache(cache_key, cache_data, ttl=604800)  # 缓存7天
            logger.info(f"Cached daily pool results for {today}")

        except Exception as e:
            logger.error(f"Error caching daily pool results: {e}")

    async def get_latest_pool(self) -> Optional[Dict]:
        """获取最新的日筛选池"""
        try:
            # 先从缓存获取
            today = datetime.now().strftime('%Y%m%d')
            cache_key = f"daily_pool:{today}"
            cached_data = await get_cache(cache_key)
            if cached_data:
                return cached_data

            # 从数据库获取
            stmt = select(DailyPool).where(
                DailyPool.scan_date == datetime.now().date()
            ).order_by(DailyPool.stock_code)

            result = await self.db.execute(stmt)
            pools = result.scalars().all()

            if not pools:
                return None

            return {
                'scan_date': datetime.now().date(),
                'pool_count': len(pools),
                'results': [
                    {
                        'code': p.stock_code,
                        'name': p.stock_name,
                        'vol_ma20': p.vol_ma20,
                        'vol_ma60': p.vol_ma60,
                        'golden_cross': p.golden_cross,
                        'macd_120min_status': p.macd_120min_status
                    }
                    for p in pools
                ]
            }

        except Exception as e:
            logger.error(f"Error getting latest daily pool: {e}")
            return None

    async def update_daily_klines(self):
        """更新日线数据（包括均量线）"""
        try:
            logger.info("Updating daily klines with volume MA...")

            # 获取所有股票代码
            stmt = select(Stock.code)
            result = await self.db.execute(stmt)
            stock_codes = result.scalars().all()

            updated_count = 0

            for stock_code in stock_codes:
                try:
                    # 获取最新日线数据
                    stmt = select(DailyKline).where(
                        DailyKline.stock_code == stock_code
                    ).order_by(DailyKline.trade_date.desc()).limit(100)

                    result = await self.db.execute(stmt)
                    klines = result.scalars().all()

                    if len(klines) >= 60:  # 至少有60天数据
                        # 更新均量线
                        df = pd.DataFrame([{
                            'date': k.trade_date,
                            'volume': k.volume
                        } for k in reversed(klines)])

                        # 计算均量线
                        df['vol_ma20'] = calculate_ma(df['volume'], 20)
                        df['vol_ma60'] = calculate_ma(df['volume'], 60)

                        # 更新数据库
                        for i, kline in enumerate(klines):
                            if i >= 60:  # 从第60天开始更新
                                kline.vol_ma20 = int(df['vol_ma20'].iloc[i])
                                kline.vol_ma60 = int(df['vol_ma60'].iloc[i])

                        updated_count += 1

                except Exception as e:
                    logger.error(f"Error updating daily kline for {stock_code}: {e}")

            await self.db.commit()
            logger.info(f"Updated volume MA for {updated_count} stocks")

        except Exception as e:
            logger.error(f"Error updating daily klines: {e}")
            await self.db.rollback()

    async def update_120min_macd(self):
        """更新120分钟MACD数据"""
        try:
            logger.info("Updating 120min MACD data...")

            # 获取日筛选池中的股票
            today = datetime.now().date()
            stmt = select(DailyPool.stock_code).where(
                DailyPool.scan_date == today
            ).distinct()

            result = await self.db.execute(stmt)
            stock_codes = result.scalars().all()

            updated_count = 0

            for stock_code in stock_codes:
                try:
                    # 获取最新的120分钟K线
                    stmt = select(Kline120min).where(
                        Kline120min.stock_code == stock_code
                    ).order_by(Kline120min.datetime.desc()).limit(50)

                    result = await self.db.execute(stmt)
                    klines = result.scalars().all()

                    if len(klines) >= 26:  # 至少需要26根K线计算MACD
                        # 计算MACD
                        df = pd.DataFrame([{
                            'close': k.close
                        } for k in reversed(klines)])

                        macd_data = calculate_macd(df['close'])

                        # 更新最新的MACD值
                        for i, kline in enumerate(klines):
                            if i >= len(macd_data):
                                break
                            kline.macd = float(macd_data['macd'].iloc[i])
                            kline.macd_signal = float(macd_data['macd_signal'].iloc[i])
                            kline.macd_hist = float(macd_data['macd_hist'].iloc[i])

                        updated_count += 1

                except Exception as e:
                    logger.error(f"Error updating 120min MACD for {stock_code}: {e}")

            await self.db.commit()
            logger.info(f"Updated MACD for {updated_count} stocks")

        except Exception as e:
            logger.error(f"Error updating 120min MACD: {e}")
            await self.db.rollback()