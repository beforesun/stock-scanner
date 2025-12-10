#!/usr/bin/env python3
"""
初始化股票列表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import AsyncSessionLocal
from app.models.stock import Stock
from app.utils.helpers import setup_logging

logger = setup_logging('init_stock_list')

async def init_stock_list():
    """初始化股票列表"""
    logger.info("Starting stock list initialization...")

    try:
        import akshare as ak

        # 获取A股列表
        logger.info("Fetching stock list from AKShare...")
        stock_info = ak.stock_zh_a_spot_em()

        if stock_info.empty:
            logger.error("Failed to fetch stock list")
            return

        # 只保留A股代码
        stock_info = stock_info[stock_info['代码'].str.match(r'^(60|00|30)\d{4}$')]

        logger.info(f"Found {len(stock_info)} stocks")

        # 保存到数据库
        async with AsyncSessionLocal() as db:
            # 清空现有数据
            logger.info("Clearing existing stock data...")
            await db.execute("TRUNCATE TABLE stocks RESTART IDENTITY CASCADE")
            await db.commit()

            # 批量插入
            logger.info("Inserting stock data...")
            for _, row in stock_info.iterrows():
                code = row['代码']
                name = row['名称']

                # 判断市场
                market = 'SH' if code.startswith('6') else 'SZ'

                stock = Stock(
                    code=code,
                    name=name,
                    market=market
                )
                db.add(stock)

            await db.commit()

        logger.info(f"Successfully initialized {len(stock_info)} stocks")

    except Exception as e:
        logger.error(f"Error initializing stock list: {e}")
        raise

async def main():
    """主函数"""
    await init_stock_list()

if __name__ == "__main__":
    asyncio.run(main())