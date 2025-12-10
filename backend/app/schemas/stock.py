from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class StockBase(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: Optional[str] = Field(None, description="市场代码 SH/SZ")

class StockCreate(StockBase):
    pass

class StockResponse(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KlineData(BaseModel):
    date: date = Field(..., description="交易日期")
    open: Decimal = Field(..., description="开盘价")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")

class WeeklyKlineData(KlineData):
    ma233: Optional[Decimal] = Field(None, description="233周均线")
    vol_ma20: Optional[int] = Field(None, description="周成交量MA20")

class DailyKlineData(KlineData):
    vol_ma20: Optional[int] = Field(None, description="20日均量")
    vol_ma60: Optional[int] = Field(None, description="60日均量")

class Kline120minData(BaseModel):
    datetime: datetime = Field(..., description="时间戳")
    open: Decimal = Field(..., description="开盘价")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    macd: Optional[Decimal] = Field(None, description="MACD值")
    macd_signal: Optional[Decimal] = Field(None, description="MACD信号线")
    macd_hist: Optional[Decimal] = Field(None, description="MACD柱状图")

class StockDetailResponse(BaseModel):
    code: str
    name: str
    market: Optional[str]
    latest_price: Optional[Decimal] = Field(None, description="最新价格")
    in_weekend_pool: bool = Field(False, description="是否在周末筛选池中")
    in_daily_pool: bool = Field(False, description="是否在日常筛选池中")
    has_signal: bool = Field(False, description="是否有交易信号")

class StockKlineRequest(BaseModel):
    type: str = Field(..., description="K线类型: daily, weekly, 120min")
    days: Optional[int] = Field(60, description="返回天数", ge=1, le=365)
    weeks: Optional[int] = Field(None, description="返回周数（仅周线有效）", ge=1, le=104)

class StockKlineResponse(BaseModel):
    code: str
    name: str
    type: str
    data: List[Union[DailyKlineData, WeeklyKlineData, Kline120minData]]