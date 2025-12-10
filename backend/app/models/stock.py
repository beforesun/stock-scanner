from sqlalchemy import Column, Integer, String, DateTime, Date, DECIMAL, BigInteger, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    market = Column(String(10))  # 'SH' or 'SZ'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联
    weekly_klines = relationship("WeeklyKline", back_populates="stock", cascade="all, delete-orphan")
    daily_klines = relationship("DailyKline", back_populates="stock", cascade="all, delete-orphan")
    kline_120min = relationship("Kline120min", back_populates="stock", cascade="all, delete-orphan")
    weekend_scan_results = relationship("WeekendScanResult", back_populates="stock", cascade="all, delete-orphan")
    daily_pool = relationship("DailyPool", back_populates="stock", cascade="all, delete-orphan")
    limit_up_records = relationship("LimitUpRecord", back_populates="stock", cascade="all, delete-orphan")
    trade_signals = relationship("TradeSignal", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock(code='{self.code}', name='{self.name}')>"

class WeeklyKline(Base):
    __tablename__ = "weekly_klines"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    trade_date = Column(Date, nullable=False)
    open = Column(DECIMAL(10, 2))
    high = Column(DECIMAL(10, 2))
    low = Column(DECIMAL(10, 2))
    close = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    ma233 = Column(DECIMAL(10, 2))  # 233周均线
    vol_ma20 = Column(BigInteger)  # 周成交量MA20

    # 关联
    stock = relationship("Stock", back_populates="weekly_klines")

    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date"),
        Index("idx_weekly_klines_code_date", "stock_code", "trade_date"),
    )

class DailyKline(Base):
    __tablename__ = "daily_klines"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    trade_date = Column(Date, nullable=False)
    open = Column(DECIMAL(10, 2))
    high = Column(DECIMAL(10, 2))
    low = Column(DECIMAL(10, 2))
    close = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    vol_ma20 = Column(BigInteger)  # 20日均量
    vol_ma60 = Column(BigInteger)  # 60日均量

    # 关联
    stock = relationship("Stock", back_populates="daily_klines")

    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date"),
        Index("idx_daily_klines_code_date", "stock_code", "trade_date"),
    )

class Kline120min(Base):
    __tablename__ = "kline_120min"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    datetime = Column(DateTime, nullable=False)
    open = Column(DECIMAL(10, 2))
    high = Column(DECIMAL(10, 2))
    low = Column(DECIMAL(10, 2))
    close = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    macd = Column(DECIMAL(10, 4))
    macd_signal = Column(DECIMAL(10, 4))
    macd_hist = Column(DECIMAL(10, 4))  # 红绿柱

    # 关联
    stock = relationship("Stock", back_populates="kline_120min")

    __table_args__ = (
        UniqueConstraint("stock_code", "datetime"),
        Index("idx_120min_code_datetime", "stock_code", "datetime"),
    )