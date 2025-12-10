from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services.daily_scanner import DailyScanner
from app.services.weekend_scanner import WeekendScanner
from app.utils.redis_client import get_redis
from app.schemas.signal import DailyPoolResponse, DailyPoolResult

router = APIRouter()

@router.get("/latest", response_model=DailyPoolResponse)
async def get_latest_daily_pool(db: AsyncSession = Depends(get_db)):
    """获取最新的日筛选池"""
    redis = await get_redis()
    scanner = DailyScanner(db, redis)

    result = await scanner.get_latest_pool()

    if not result:
        # 如果没有日筛选池数据，尝试从周末结果重新筛选
        weekend_scanner = WeekendScanner(db, redis)
        weekend_results = await weekend_scanner.get_latest_results()

        if not weekend_results:
            raise HTTPException(status_code=404, detail="No scan results found")

        # 执行日筛选
        result = await scanner.scan_daily_pool(weekend_results['results'])

    return DailyPoolResponse(
        scan_date=result['scan_date'],
        total_count=result['total_count'] if 'total_count' in result else len(result['results']),
        pool_count=len(result['results']),
        results=[DailyPoolResult(**r) for r in result['results']]
    )

@router.post("/trigger")
async def trigger_daily_scan(db: AsyncSession = Depends(get_db)):
    """手动触发日筛选"""
    redis = await get_redis()

    # 获取最新的周末扫描结果
    weekend_scanner = WeekendScanner(db, redis)
    weekend_results = await weekend_scanner.get_latest_results()

    if not weekend_results:
        raise HTTPException(status_code=404, detail="No weekend scan results found")

    # 执行日筛选
    daily_scanner = DailyScanner(db, redis)
    result = await daily_scanner.scan_daily_pool(weekend_results['results'])

    return {
        "message": "Daily scan completed successfully",
        "scan_date": result['scan_date'],
        "pool_count": result['pool_count'],
        "duration": result['duration']
    }