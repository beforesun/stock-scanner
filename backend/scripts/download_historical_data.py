#!/usr/bin/env python3
"""
下载历史数据
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import AsyncSessionLocal
from app.models.stock import Stock, DailyKline, WeeklyKline
from app.utils.helpers import setup_logging
from app.utils.indicators import calculate_ma

logger = setup_logging('download_historical_data')

async def download_daily_data(stock_code: str, days: int = 365):
    """下载日线数据"""
    try:
        import akshare as ak

        logger.info(f"Downloading daily data for {stock_code}...")

        # 获取日线数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )

        if df.empty:
            logger.warning(f"No daily data found for {stock_code}")
            return []

        # 重命名列
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })

        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date

        # 计算均量线
        df['vol_ma20'] = calculate_ma(df['volume'], 20)
        df['vol_ma60'] = calculate_ma(df['volume'], 60)

        # 转换为字典列表
        records = []
        for _, row in df.iterrows():
            records.append({
                'stock_code': stock_code,
                'trade_date': row['trade_date'],
                'open': row['open'],
                'close': row['close'],
                'high': row['high'],
                'low': row['low'],
                'volume': int(row['volume']),
                'vol_ma20': int(row['vol_ma20']) if not pd.isna(row['vol_ma20']) else None,
                'vol_ma60': int(row['vol_ma60']) if not pd.isna(row['vol_ma60']) else None
            })

        return records

    except Exception as e:
        logger.error(f"Error downloading daily data for {stock_code}: {e}")
        return []

async def download_weekly_data(stock_code: str, weeks: int = 104):
    """下载周线数据"""
    try:
        import akshare as ak

        logger.info(f"Downloading weekly data for {stock_code}...")

        # 获取周线数据
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="weekly",
            adjust="qfq"
        )

        if df.empty:
            logger.warning(f"No weekly data found for {stock_code}")
            return []

        # 只保留最近N周
        if len(df) > weeks:
            df = df.tail(weeks)

        # 重命名列
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })

        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date

        # 计算233周均线和20周均量
        df['ma233'] = calculate_ma(df['close'], 233)
        df['vol_ma20'] = calculate_ma(df['volume'], 20)

        # 转换为字典列表
        records = []
        for _, row in df.iterrows():
            records.append({
                'stock_code': stock_code,
                'trade_date': row['trade_date'],
                'open': row['open'],
                'close': row['close'],
                'high': row['high'],
                'low': row['low'],
                'volume': int(row['volume']),
                'ma233': row['ma233'] if not pd.isna(row['ma233']) else None,
                'vol_ma20': int(row['vol_ma20']) if not pd.isna(row['vol_ma20']) else None
            })

        return records

    except Exception as e:
        logger.error(f"Error downloading weekly data for {stock_code}: {e}")
        return []

async def save_daily_data(db, records: list):
    """保存日线数据"""
    if not records:
        return

    try:
        # 清空现有数据
        stock_code = records[0]['stock_code']
        await db.execute(
            f"DELETE FROM daily_klines WHERE stock_code = '{stock_code}'"
        )

        # 批量插入
        for record in records:
            kline = DailyKline(**record)
            db.add(kline)

        await db.commit()
        logger.info(f"Saved {len(records)} daily klines for {stock_code}")

    except Exception as e:
        logger.error(f"Error saving daily data: {e}")
        await db.rollback()
        raise

async def save_weekly_data(db, records: list):
    """保存周线数据"""
    if not records:
        return

    try:
        # 清空现有数据
        stock_code = records[0]['stock_code']
        await db.execute(
            f"DELETE FROM weekly_klines WHERE stock_code = '{stock_code}'"
        )

        # 批量插入
        for record in records:
            kline = WeeklyKline(**record)
            db.add(kline)

        await db.commit()
        logger.info(f"Saved {len(records)} weekly klines for {stock_code}")

    except Exception as e:
        logger.error(f"Error saving weekly data: {e}")
        await db.rollback()
        raise

async def download_all_stocks():
    """下载所有股票的历史数据"""
    logger.info("Starting historical data download...")

    async with AsyncSessionLocal() as db:
        try:
            # 获取所有股票代码
            from sqlalchemy import select
            result = await db.execute(select(Stock.code, Stock.name))
            stocks = result.all()

            logger.info(f"Found {len(stocks)} stocks to download")

            # 分批处理
            batch_size = 50
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(stocks)-1)//batch_size + 1}")

                for stock_code, stock_name in batch:
                    try:
                        # 下载日线数据
                        daily_records = await download_daily_data(stock_code)
                        if daily_records:
                            await save_daily_data(db, daily_records)

                        # 下载周线数据
                        weekly_records = await download_weekly_data(stock_code)
                        if weekly_records:
                            await save_weekly_data(db, weekly_records)

                    except Exception as e:
                        logger.error(f"Error processing {stock_code}: {e}")
                        continue

                # 短暂休眠，避免请求过快
                await asyncio.sleep(1)

            logger.info("Historical data download completed")

        except Exception as e:
            logger.error(f"Error downloading historical data: {e}")
            raise

async def main():
    """主函数"""
    await download_all_stocks()

if __name__ == "__main__":
    asyncio.run(main())