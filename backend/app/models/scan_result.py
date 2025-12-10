from sqlalchemy import Column, Integer, String, DateTime, Date, DECIMAL, BigInteger, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class WeekendScanResult(Base):
    __tablename__ = "weekend_scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_date = Column(Date, nullable=False)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    stock_name = Column(String(50))
    close_price = Column(DECIMAL(10, 2))
    ma233_weekly = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    vol_ma20_weekly = Column(BigInteger)
    pass_condition = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    stock = relationship("Stock", back_populates="weekend_scan_results")

    __table_args__ = (
        Index("idx_weekend_scan_date", "scan_date"),
    )

class DailyPool(Base):
    __tablename__ = "daily_pool"

    id = Column(Integer, primary_key=True, index=True)
    scan_date = Column(Date, nullable=False)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    stock_name = Column(String(50))
    vol_ma20 = Column(BigInteger)
    vol_ma60 = Column(BigInteger)
    golden_cross = Column(Boolean)  # 均量线金叉
    macd_120min_status = Column(String(50))  # MACD红柱状态
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    stock = relationship("Stock", back_populates="daily_pool")

    __table_args__ = (
        Index("idx_daily_pool_date", "scan_date"),
    )

class LimitUpRecord(Base):
    __tablename__ = "limit_up_records"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    limit_date = Column(Date, nullable=False)
    limit_price = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)

    # 关联
    stock = relationship("Stock", back_populates="limit_up_records")

    __table_args__ = (
        UniqueConstraint("stock_code", "limit_date"),
    )