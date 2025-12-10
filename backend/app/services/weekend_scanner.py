import akshare as ak
import pandas as pd
from typing import List, Dict, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func, and_

from app.database import AsyncSessionLocal
from app.models.stock import Stock
from app.models.scan_result import WeekendScanResult
from app.utils.indicators import calculate_ma
from app.utils.helpers import is_trading_day, get_trading_calendar
from app.utils.redis_client import get_cache, set_cache
from app.config import settings

logger = logging.getLogger(__name__)

class WeekendScanner:
    """周末全市场扫描器"""

    def __init__(self, db_session: AsyncSession, redis_client):
        self.db = db_session
        self.redis = redis_client
        self.max_workers = settings.max_workers
        self.ma_period = settings.ma_period_weekly
        self.vol_ma_period = settings.vol_ma_period_weekly

    async def scan_all_stocks(self) -> Dict:
        """
        扫描全部A股，筛选符合条件的股票
        条件: 收盘价 > 233周均线 且 周成交量 > 周MA20
        """
        logger.info("Starting weekend scan...")
        start_time = datetime.now()

        # 1. 获取所有A股代码
        stock_list = await self._get_all_stocks()
        logger.info(f"Total stocks to scan: {len(stock_list)}")

        # 2. 并行处理每只股票
        results = []

        # 使用异步任务处理
        tasks = []
        for stock_code in stock_list:
            task = asyncio.create_task(self._scan_single_stock_async(stock_code))
            tasks.append(task)

            # 限制并发数量
            if len(tasks) >= self.max_workers:
                completed = await asyncio.gather(*tasks[:self.max_workers])
                for result in completed:
                    if result and result['pass_condition']:
                        results.append(result)
                tasks = tasks[self.max_workers:]

        # 处理剩余任务
        if tasks:
            completed = await asyncio.gather(*tasks)
            for result in completed:
                if result and result['pass_condition']:
                    results.append(result)

        # 3. 保存结果到数据库
        await self._save_results(results)

        # 4. 缓存到Redis
        await self._cache_results(results)

        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()

        logger.info(f"Weekend scan completed in {scan_duration:.2f} seconds")
        logger.info(f"Total scanned: {len(stock_list)}, Passed: {len(results)}")

        return {
            'scan_date': datetime.now().date(),
            'total_scanned': len(stock_list),
            'passed_count': len(results),
            'results': results,
            'duration': scan_duration
        }

    async def _scan_single_stock_async(self, stock_code: str) -> Optional[Dict]:
        """异步扫描单只股票"""
        try:
            # 检查缓存
            cache_key = f"weekend_scan:{stock_code}:{datetime.now().strftime('%Y%m%d')}"
            cached_result = await get_cache(cache_key)
            if cached_result:
                return cached_result

            # 获取周线数据
            df_weekly = await self._get_weekly_data(stock_code)

            if df_weekly is None or len(df_weekly) < self.ma_period:
                return None

            # 计算指标
            df_weekly['ma233'] = calculate_ma(df_weekly['close'], self.ma_period)
            df_weekly['vol_ma20'] = calculate_ma(df_weekly['volume'], self.vol_ma_period)

            # 最新一周数据
            latest = df_weekly.iloc[-1]

            # 判断条件
            pass_condition = (
                latest['close'] > latest['ma233'] and
                latest['volume'] > latest['vol_ma20']
            )

            if pass_condition:
                result = {
                    'code': stock_code,
                    'name': await self._get_stock_name(stock_code),
                    'close_price': float(latest['close']),
                    'ma233_weekly': float(latest['ma233']),
                    'volume': int(latest['volume']),
                    'vol_ma20_weekly': int(latest['vol_ma20']),
                    'pass_condition': True
                }

                # 缓存结果（7天）
                await set_cache(cache_key, result, ttl=604800)

                return result

            return None

        except Exception as e:
            logger.error(f"Error scanning {stock_code}: {e}")
            return None

    def _scan_single_stock(self, stock_code: str) -> Optional[Dict]:
        """扫描单只股票（同步版本，用于进程池）"""
        try:
            # 获取周线数据
            df_weekly = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",
                adjust="qfq"
            )

            if df_weekly is None or len(df_weekly) < self.ma_period:
                return None

            # 重命名列
            df_weekly = df_weekly.rename(columns={
                '收盘': 'close',
                '成交量': 'volume'
            })

            # 计算指标
            df_weekly['ma233'] = calculate_ma(df_weekly['close'], self.ma_period)
            df_weekly['vol_ma20'] = calculate_ma(df_weekly['volume'], self.vol_ma_period)

            # 最新一周数据
            latest = df_weekly.iloc[-1]

            # 判断条件
            pass_condition = (
                latest['close'] > latest['ma233'] and
                latest['volume'] > latest['vol_ma20']
            )

            if pass_condition:
                return {
                    'code': stock_code,
                    'name': self._get_stock_name_sync(stock_code),
                    'close_price': float(latest['close']),
                    'ma233_weekly': float(latest['ma233']),
                    'volume': int(latest['volume']),
                    'vol_ma20_weekly': int(latest['vol_ma20']),
                    'pass_condition': True
                }

            return None

        except Exception as e:
            logger.error(f"Error scanning {stock_code}: {e}")
            return None

    async def _get_weekly_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取周线数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",
                adjust="qfq"
            )

            if df is None or df.empty:
                return None

            # 重命名列
            df = df.rename(columns={
                '收盘': 'close',
                '成交量': 'volume'
            })

            return df[['close', 'volume']]

        except Exception as e:
            logger.error(f"Error getting weekly data for {stock_code}: {e}")
            return None

    async def _get_all_stocks(self) -> List[str]:
        """获取所有A股代码"""
        # 从数据库获取，如果没有则从API获取
        stmt = select(Stock.code)
        result = await self.db.execute(stmt)
        stocks = result.scalars().all()

        if stocks:
            return list(stocks)

        # 从API获取股票列表
        try:
            stock_info = ak.stock_zh_a_spot_em()
            if stock_info is not None and not stock_info.empty:
                stocks = stock_info['代码'].tolist()
                # 保存到数据库
                for _, row in stock_info.iterrows():
                    stock = Stock(
                        code=row['代码'],
                        name=row['名称'],
                        market='SH' if row['代码'].startswith('6') else 'SZ'
                    )
                    self.db.add(stock)
                await self.db.commit()
                return stocks
        except Exception as e:
            logger.error(f"Error getting stock list: {e}")

        # 返回默认列表
        return ['600519', '000858', '000002', '600036', '000001']

    def _get_stock_name_sync(self, stock_code: str) -> str:
        """同步获取股票名称"""
        try:
            # 从缓存的股票列表中获取
            stock_info = ak.stock_zh_a_spot_em()
            if stock_info is not None and not stock_info.empty:
                stock = stock_info[stock_info['代码'] == stock_code]
                if not stock.empty:
                    return stock['名称'].iloc[0]
        except:
            pass
        return stock_code

    async def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        # 先从数据库查询
        stmt = select(Stock.name).where(Stock.code == stock_code)
        result = await self.db.execute(stmt)
        name = result.scalar_one_or_none()
        if name:
            return name

        # 从API获取
        return self._get_stock_name_sync(stock_code)

    async def _save_results(self, results: List[Dict]):
        """保存扫描结果到数据库"""
        if not results:
            return

        try:
            # 先删除今天的记录
            today = datetime.now().date()
            await self.db.execute(
                WeekendScanResult.__table__.delete().where(
                    WeekendScanResult.scan_date == today
                )
            )

            # 插入新记录
            for result in results:
                scan_result = WeekendScanResult(
                    scan_date=today,
                    stock_code=result['code'],
                    stock_name=result['name'],
                    close_price=result['close_price'],
                    ma233_weekly=result['ma233_weekly'],
                    volume=result['volume'],
                    vol_ma20_weekly=result['vol_ma20_weekly'],
                    pass_condition=True
                )
                self.db.add(scan_result)

            await self.db.commit()
            logger.info(f"Saved {len(results)} weekend scan results")

        except Exception as e:
            logger.error(f"Error saving weekend scan results: {e}")
            await self.db.rollback()
            raise

    async def _cache_results(self, results: List[Dict]):
        """缓存结果到Redis"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            cache_key = f"weekend_scan:{today}"

            # 只缓存基本信息
            cache_data = {
                'scan_date': today,
                'total_count': len(results),
                'results': [
                    {
                        'code': r['code'],
                        'name': r['name'],
                        'close_price': r['close_price'],
                        'ma233_weekly': r['ma233_weekly']
                    }
                    for r in results
                ]
            }

            await set_cache(cache_key, cache_data, ttl=604800)  # 缓存7天
            logger.info(f"Cached weekend scan results for {today}")

        except Exception as e:
            logger.error(f"Error caching weekend scan results: {e}")

    async def get_latest_results(self) -> Optional[Dict]:
        """获取最新的扫描结果"""
        try:
            # 先从缓存获取
            today = datetime.now().strftime('%Y%m%d')
            cache_key = f"weekend_scan:{today}"
            cached_data = await get_cache(cache_key)
            if cached_data:
                return cached_data

            # 从数据库获取
            stmt = select(WeekendScanResult).where(
                WeekendScanResult.scan_date == datetime.now().date()
            ).order_by(WeekendScanResult.stock_code)

            result = await self.db.execute(stmt)
            results = result.scalars().all()

            if not results:
                return None

            return {
                'scan_date': datetime.now().date(),
                'total_count': len(results),
                'results': [
                    {
                        'code': r.stock_code,
                        'name': r.stock_name,
                        'close_price': float(r.close_price),
                        'ma233_weekly': float(r.ma233_weekly),
                        'volume': r.volume,
                        'vol_ma20_weekly': r.vol_ma20_weekly
                    }
                    for r in results
                ]
            }

        except Exception as e:
            logger.error(f"Error getting latest weekend scan results: {e}")
            return None

    async def get_history_results(self, page: int = 1, size: int = 20) -> Dict:
        """获取历史扫描记录"""
        try:
            # 获取不同日期的扫描记录
            stmt = select(
                WeekendScanResult.scan_date,
                func.count(WeekendScanResult.id).label('count')
            ).group_by(
                WeekendScanResult.scan_date
            ).order_by(
                WeekendScanResult.scan_date.desc()
            ).offset((page - 1) * size).limit(size)

            result = await self.db.execute(stmt)
            records = result.all()

            return {
                'page': page,
                'size': size,
                'records': [
                    {
                        'scan_date': str(r.scan_date),
                        'count': r.count
                    }
                    for r in records
                ]
            }

        except Exception as e:
            logger.error(f"Error getting history results: {e}")
            return {'page': page, 'size': size, 'records': []}