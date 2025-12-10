from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from app.services.signal_generator import SignalGenerator
from app.utils.redis_client import get_redis
from app.schemas.signal import (
    SignalListResponse,
    TradeSignalResponse,
    SignalStatusUpdate,
    SignalStatus
)

router = APIRouter()

@router.get("/latest", response_model=SignalListResponse)
async def get_latest_signals(
    status: Optional[str] = Query(None, description="Filter by signal status"),
    db: AsyncSession = Depends(get_db)
):
    """获取最新的交易信号"""
    generator = SignalGenerator()

    result = await generator.get_today_signals(status)

    if not result:
        return SignalListResponse(
            signal_date=datetime.now().date(),
            total_signals=0,
            signals=[]
        )

    return SignalListResponse(
        signal_date=result['signal_date'],
        total_signals=result['total_signals'],
        signals=[TradeSignalResponse(**s) for s in result['signals']]
    )

@router.get("/{signal_id}", response_model=TradeSignalResponse)
async def get_signal_detail(
    signal_id: int = Path(..., description="Signal ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取信号详情"""
    from app.services.pattern_recognizer import PatternRecognizer

    redis = await get_redis()
    recognizer = PatternRecognizer(db, redis)

    signal = await recognizer.get_signal_detail(signal_id)

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    return TradeSignalResponse(**signal)

@router.put("/{signal_id}/status")
async def update_signal_status(
    signal_id: int = Path(..., description="Signal ID"),
    status_update: SignalStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新信号状态"""
    from app.services.pattern_recognizer import PatternRecognizer

    redis = await get_redis()
    recognizer = PatternRecognizer(db, redis)

    success = await recognizer.update_signal_status(
        signal_id,
        status_update.status,
        status_update.note
    )

    if not success:
        raise HTTPException(status_code=404, detail="Signal not found")

    return {"message": "Signal status updated successfully"}

@router.get("/history/{days}")
async def get_signal_history(
    days: int = Path(..., description="Number of days to look back", ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """获取信号历史记录"""
    generator = SignalGenerator()

    signals = await generator.get_signal_history(days)

    return {
        "days": days,
        "total_signals": len(signals),
        "signals": [TradeSignalResponse(**s) for s in signals]
    }