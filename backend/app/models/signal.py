from sqlalchemy import Column, Integer, String, DateTime, Date, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class TradeSignal(Base):
    __tablename__ = "trade_signals"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False)
    stock_name = Column(String(50))
    signal_type = Column(String(20), nullable=False)  # 'BUY', 'SELL'
    signal_date = Column(Date, nullable=False)
    signal_price = Column(DECIMAL(10, 2))

    # 买入信号相关字段
    limit_up_date = Column(Date)  # 涨停板日期
    pullback_days = Column(Integer)  # 回调天数
    volume_ratio = Column(DECIMAL(5, 2))  # 放量倍数
    price_change = Column(DECIMAL(5, 2))  # 涨幅
    upper_shadow = Column(DECIMAL(5, 2))  # 上影线占比

    # 止损价格
    stop_loss_price = Column(DECIMAL(10, 2))
    stop_loss_reason = Column(String(100))

    # 状态
    status = Column(String(20), default='PENDING')  # PENDING, CONFIRMED, INVALID
    reason = Column(String)  # TEXT type

    created_at = Column(DateTime(timezone=True), server_default='now()')

    # 关联
    stock = relationship("Stock", back_populates="trade_signals")

    __table_args__ = (
        Index('idx_signals_date', 'signal_date'),
        Index('idx_signals_status', 'status'),
    )

    def __repr__(self):
        return f"<TradeSignal(code='{self.stock_code}', type='{self.signal_type}', date='{self.signal_date}')>"