from fastapi import APIRouter, HTTPException, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from app.services.data_fetcher import DataFetcher
from app.utils.redis_client import get_cache, set_cache
from app.schemas.stock import StockDetailResponse, StockKlineResponse, StockKlineRequest
from app.config import settings

router = APIRouter()

@router.get("/{code}", response_model=StockDetailResponse)
async def get_stock_detail(
    code: str = Path(..., description="Stock code"),
    db: AsyncSession = Depends(get_db)
):
    """获取个股详情"""
    from app.models.stock import Stock
    from app.models.scan_result import WeekendScanResult, DailyPool
    from app.models.signal import TradeSignal
    from sqlalchemy import select, and_, func

    # 获取股票基本信息
    stmt = select(Stock).where(Stock.code == code)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # 检查是否在周末筛选池中
    today = datetime.now().date()
    stmt = select(func.count(WeekendScanResult.id)).where(
        and_(
            WeekendScanResult.stock_code == code,
            WeekendScanResult.scan_date == today
        )
    )
    result = await db.execute(stmt)
    in_weekend_pool = result.scalar() > 0

    # 检查是否在日筛选池中
    stmt = select(func.count(DailyPool.id)).where(
        and_(
            DailyPool.stock_code == code,
            DailyPool.scan_date == today
        )
    )
    result = await db.execute(stmt)
    in_daily_pool = result.scalar() > 0

    # 检查是否有交易信号
    stmt = select(func.count(TradeSignal.id)).where(
        and_(
            TradeSignal.stock_code == code,
            TradeSignal.signal_date == today,
            TradeSignal.status == 'PENDING'
        )
    )
    result = await db.execute(stmt)
    has_signal = result.scalar() > 0

    # 获取最新价格（这里简化处理，实际应该从实时数据源获取）
    latest_price = None

    return StockDetailResponse(
        code=stock.code,
        name=stock.name,
        market=stock.market,
        latest_price=latest_price,
        in_weekend_pool=in_weekend_pool,
        in_daily_pool=in_daily_pool,
        has_signal=has_signal
    )

@router.get("/{code}/klines", response_model=StockKlineResponse)
async def get_stock_klines(
    code: str = Path(..., description="Stock code"),
    request: StockKlineRequest = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取个股K线数据"""
    from app.models.stock import Stock, DailyKline, WeeklyKline, Kline120min
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta

    # 验证股票是否存在
    stmt = select(Stock).where(Stock.code == code)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # 根据类型获取不同的K线数据
    if request.type == "daily":
        # 获取日线数据
        if request.days:
            start_date = datetime.now().date() - timedelta(days=request.days)
            stmt = select(DailyKline).where(
                and_(
                    DailyKline.stock_code == code,
                    DailyKline.trade_date >= start_date
                )
            ).order_by(DailyKline.trade_date.desc())
        else:
            stmt = select(DailyKline).where(
                DailyKline.stock_code == code
            ).order_by(DailyKline.trade_date.desc())

        result = await db.execute(stmt)
        klines = result.scalars().all()

        # 转换为响应格式
        data = [{
            "date": k.trade_date,
            "open": float(k.open),
            "close": float(k.close),
            "high": float(k.high),
            "low": float(k.low),
            "volume": k.volume,
            "vol_ma20": k.vol_ma20,
            "vol_ma60": k.vol_ma60
        } for k in klines]

    elif request.type == "weekly":
        # 获取周线数据
        if request.weeks:
            start_date = datetime.now().date() - timedelta(weeks=request.weeks)
            stmt = select(WeeklyKline).where(
                and_(
                    WeeklyKline.stock_code == code,
                    WeeklyKline.trade_date >= start_date
                )
            ).order_by(WeeklyKline.trade_date.desc())
        else:
            stmt = select(WeeklyKline).where(
                WeeklyKline.stock_code == code
            ).order_by(WeeklyKline.trade_date.desc())

        result = await db.execute(stmt)
        klines = result.scalars().all()

        # 转换为响应格式
        data = [{
            "date": k.trade_date,
            "open": float(k.open),
            "close": float(k.close),
            "high": float(k.high),
            "low": float(k.low),
            "volume": k.volume,
            "ma233": float(k.ma233) if k.ma233 else None,
            "vol_ma20": k.vol_ma20
        } for k in klines]

    elif request.type == "120min":
        # 获取120分钟K线数据
        if request.days:
            start_datetime = datetime.now() - timedelta(days=request.days)
            stmt = select(Kline120min).where(
                and_(
                    Kline120min.stock_code == code,
                    Kline120min.datetime >= start_datetime
                )
            ).order_by(Kline120min.datetime.desc())
        else:
            stmt = select(Kline120min).where(
                Kline120min.stock_code == code
            ).order_by(Kline120min.datetime.desc())

        result = await db.execute(stmt)
        klines = result.scalars().all()

        # 转换为响应格式
        data = [{
            "datetime": k.datetime,
            "open": float(k.open),
            "close": float(k.close),
            "high": float(k.high),
            "low": float(k.low),
            "volume": k.volume,
            "macd": float(k.macd) if k.macd else None,
            "macd_signal": float(k.macd_signal) if k.macd_signal else None,
            "macd_hist": float(k.macd_hist) if k.macd_hist else None
        } for k in klines]

    else:
        raise HTTPException(status_code=400, detail="Invalid kline type")

    return StockKlineResponse(
        code=stock.code,
        name=stock.name,
        type=request.type,
        data=data
    )