from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services.weekend_scanner import WeekendScanner
from app.utils.redis_client import get_redis
from app.schemas.signal import WeekendScanResponse, WeekendScanResult

router = APIRouter()

@router.get("/latest", response_model=WeekendScanResponse)
async def get_latest_weekend_scan(db: AsyncSession = Depends(get_db)):
    """获取最新的周末扫描结果"""
    redis = await get_redis()
    scanner = WeekendScanner(db, redis)

    result = await scanner.get_latest_results()

    if not result:
        raise HTTPException(status_code=404, detail="No weekend scan results found")

    return WeekendScanResponse(
        scan_date=result['scan_date'],
        total_count=result['total_count'],
        passed_count=len(result['results']),
        results=[WeekendScanResult(**r) for r in result['results']]
    )

@router.post("/trigger")
async def trigger_weekend_scan(db: AsyncSession = Depends(get_db)):
    """手动触发周末扫描"""
    redis = await get_redis()
    scanner = WeekendScanner(db, redis)

    try:
        result = await scanner.scan_all_stocks()
        return {
            "message": "Weekend scan completed successfully",
            "scan_date": result['scan_date'],
            "total_scanned": result['total_scanned'],
            "passed_count": result['passed_count'],
            "duration": result['duration']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.get("/history")
async def get_weekend_scan_history(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取历史扫描记录"""
    redis = await get_redis()
    scanner = WeekendScanner(db, redis)

    if page < 1 or size < 1 or size > 100:
        raise HTTPException(status_code=400, detail="Invalid page or size parameter")

    result = await scanner.get_history_results(page, size)

    return {
        "page": result['page'],
        "size": result['size'],
        "records": result['records']
    }