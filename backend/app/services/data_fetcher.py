import akshare as ak
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
from app.utils.helpers import retry

logger = logging.getLogger(__name__)

class DataFetcher:
    """数据获取器"""

    def __init__(self):
        self.default_adjust = "qfq"  # 前复权

    @retry(max_attempts=3, delay=2)
    async def fetch_daily_data(self, stock_code: str, days: int = 250) -> pd.DataFrame:
        """获取日线数据"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=self.default_adjust
            )

            if df.empty:
                logger.warning(f"No daily data found for {stock_code}")
                return pd.DataFrame()

            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching daily data for {stock_code}: {e}")
            raise

    @retry(max_attempts=3, delay=2)
    async def fetch_weekly_data(self, stock_code: str, weeks: int = 250) -> pd.DataFrame:
        """获取周线数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",
                adjust=self.default_adjust
            )

            if df.empty:
                logger.warning(f"No weekly data found for {stock_code}")
                return pd.DataFrame()

            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            # 只保留最近N周数据
            if len(df) > weeks:
                df = df.tail(weeks)

            return df

        except Exception as e:
            logger.error(f"Error fetching weekly data for {stock_code}: {e}")
            raise

    @retry(max_attempts=3, delay=2)
    async def fetch_120min_data(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """获取120分钟K线数据"""
        try:
            # AKShare没有直接的120分钟数据，使用30分钟数据并重新采样
            df = ak.stock_zh_a_hist_min_em(
                symbol=stock_code,
                period="30",
                adjust=self.default_adjust
            )

            if df.empty:
                logger.warning(f"No 30min data found for {stock_code}")
                return pd.DataFrame()

            # 重命名列
            df = df.rename(columns={
                '时间': 'datetime',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # 转换时间格式
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime').set_index('datetime')

            # 重新采样为120分钟（2小时）数据
            # 4个30分钟 = 2小时
            resampled = df.resample('2H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'amount': 'sum'
            }).dropna()

            # 重置索引
            resampled = resampled.reset_index()

            # 只保留交易时间段的数据（9:30-11:30, 13:00-15:00）
            resampled['time'] = resampled['datetime'].dt.time
            resampled = resampled[
                ((resampled['time'] >= pd.to_datetime('09:30').time()) &
                 (resampled['time'] <= pd.to_datetime('11:30').time())) |
                ((resampled['time'] >= pd.to_datetime('13:00').time()) &
                 (resampled['time'] <= pd.to_datetime('15:00').time()))
            ]

            # 只保留最近N天的数据
            cutoff_date = datetime.now() - timedelta(days=days)
            resampled = resampled[resampled['datetime'] >= cutoff_date]

            return resampled.reset_index(drop=True)

        except Exception as e:
            logger.error(f"Error fetching 120min data for {stock_code}: {e}")
            raise

    async def fetch_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            # 获取实时行情数据作为股票列表
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                logger.error("Failed to fetch stock list")
                return pd.DataFrame()

            # 只保留需要的列
            df = df[['代码', '名称']].rename(columns={
                '代码': 'code',
                '名称': 'name'
            })

            # 过滤掉非A股代码
            df = df[df['code'].str.match(r'^(60|00|30)\d{4}$')]

            return df

        except Exception as e:
            logger.error(f"Error fetching stock list: {e}")
            raise

    async def fetch_realtime_data(self, stock_codes: List[str]) -> pd.DataFrame:
        """获取实时行情数据"""
        try:
            # 批量获取实时数据
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                logger.error("Failed to fetch realtime data")
                return pd.DataFrame()

            # 过滤指定的股票
            df = df[df['代码'].isin(stock_codes)]

            # 重命名列
            df = df.rename(columns={
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            return df[['code', 'name', 'price', 'pct_change', 'volume', 'amount']]

        except Exception as e:
            logger.error(f"Error fetching realtime data: {e}")
            raise

    def get_cache_key(self, data_type: str, stock_code: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [data_type, stock_code]

        # 添加其他参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}_{value}")

        return ":".join(key_parts)