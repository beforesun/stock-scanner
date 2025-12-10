from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    INVALID = "INVALID"

class WeekendScanResult(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    close_price: Decimal = Field(..., description="收盘价")
    ma233_weekly: Decimal = Field(..., description="233周均线")
    volume: int = Field(..., description="周成交量")
    vol_ma20_weekly: int = Field(..., description="周MA20")
    condition_met: bool = Field(True, description="是否满足条件")

class WeekendScanResponse(BaseModel):
    scan_date: date = Field(..., description="扫描日期")
    total_count: int = Field(..., description="扫描总数")
    passed_count: int = Field(..., description="通过数量")
    results: List[WeekendScanResult]

class DailyPoolResult(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    vol_ma20: int = Field(..., description="20日均量")
    vol_ma60: int = Field(..., description="60日均量")
    golden_cross: bool = Field(..., description="均量线金叉")
    macd_120min_status: str = Field(..., description="120分钟MACD状态")

class DailyPoolResponse(BaseModel):
    scan_date: date = Field(..., description="扫描日期")
    total_count: int = Field(..., description="总数")
    pool_count: int = Field(..., description="筛选池数量")
    results: List[DailyPoolResult]

class TradeSignalResponse(BaseModel):
    id: int
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    signal_type: SignalType = Field(..., description="信号类型")
    signal_date: date = Field(..., description="信号日期")
    signal_price: Decimal = Field(..., description="信号价格")
    limit_up_date: Optional[date] = Field(None, description="涨停板日期")
    pullback_days: Optional[int] = Field(None, description="回调天数")
    volume_ratio: Optional[Decimal] = Field(None, description="放量倍数")
    price_change: Optional[Decimal] = Field(None, description="涨幅")
    upper_shadow: Optional[Decimal] = Field(None, description="上影线占比")
    stop_loss_price: Optional[Decimal] = Field(None, description="止损价格")
    stop_loss_reason: Optional[str] = Field(None, description="止损原因")
    status: SignalStatus = Field(SignalStatus.PENDING, description="信号状态")
    reason: Optional[str] = Field(None, description="信号理由")

class SignalListResponse(BaseModel):
    signal_date: date = Field(..., description="信号日期")
    total_signals: int = Field(..., description="信号总数")
    signals: List[TradeSignalResponse]

class SignalStatusUpdate(BaseModel):
    status: SignalStatus
    note: Optional[str] = Field(None, description="备注")

class SignalCreate(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    signal_type: SignalType = Field(..., description="信号类型")
    signal_date: date = Field(..., description="信号日期")
    signal_price: Decimal = Field(..., description="信号价格")
    limit_up_date: Optional[date] = Field(None, description="涨停板日期")
    pullback_days: Optional[int] = Field(None, description="回调天数")
    volume_ratio: Optional[Decimal] = Field(None, description="放量倍数")
    price_change: Optional[Decimal] = Field(None, description="涨幅")
    upper_shadow: Optional[Decimal] = Field(None, description="上影线占比")
    stop_loss_price: Optional[Decimal] = Field(None, description="止损价格")
    stop_loss_reason: Optional[str] = Field(None, description="止损原因")
    reason: Optional[str] = Field(None, description="信号理由")

class SystemStatus(BaseModel):
    status: str = Field(..., description="系统状态")
    last_weekend_scan: Optional[datetime] = Field(None, description="上次周末扫描时间")
    last_daily_scan: Optional[datetime] = Field(None, description="上次日筛选时间")
    next_scan: Optional[datetime] = Field(None, description="下次扫描时间")
    database_status: str = Field(..., description="数据库状态")
    redis_status: str = Field(..., description="Redis状态")