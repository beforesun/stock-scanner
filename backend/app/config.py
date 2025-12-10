from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = "postgresql://stock_user:stock_pass@localhost:5432/stock_db"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # 数据源配置
    tushare_token: Optional[str] = None

    # 任务调度配置
    weekend_scan_hour: int = 20
    weekend_scan_minute: int = 0
    daily_scan_hour: int = 15
    daily_scan_minute: int = 5

    # 并行处理配置
    max_workers: int = 8

    # 日志配置
    log_level: str = "INFO"

    # 缓存配置
    cache_ttl_daily: int = 86400  # 24小时
    cache_ttl_120min: int = 7200   # 2小时
    cache_ttl_weekend: int = 604800  # 7天

    # 股票筛选参数
    ma_period_weekly: int = 233
    vol_ma_period_weekly: int = 20
    vol_ma_period_daily_short: int = 20
    vol_ma_period_daily_long: int = 60
    macd_consecutive_days: int = 2

    # 形态识别参数
    limit_up_threshold: float = 0.098  # 涨停阈值
    breakout_volume_ratio: float = 1.8  # 放量倍数
    breakout_price_change_min: float = 0.05  # 最小涨幅
    breakout_price_change_max: float = 0.09  # 最大涨幅
    upper_shadow_threshold: float = 0.02  # 上影线阈值
    stop_loss_ratio: float = 0.90  # 止损比例

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()