import datetime
from typing import List, Optional, Dict, Any
import akshare as ak
import pandas as pd
import logging
import asyncio
from datetime import date, timedelta

logger = logging.getLogger(__name__)

def get_trading_calendar() -> pd.DataFrame:
    """获取交易日历"""
    try:
        return ak.tool_trade_date_hist_sina()
    except Exception as e:
        logger.error(f"Failed to get trading calendar: {e}")
        return pd.DataFrame()

def is_trading_day(check_date: date) -> bool:
    """判断是否为交易日"""
    try:
        calendar = get_trading_calendar()
        if calendar.empty:
            # 如果获取失败，使用简单的规则判断
            weekday = check_date.weekday()
            return weekday < 5  # 周一到周五

        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in calendar["trade_date"].astype(str).values
    except Exception as e:
        logger.error(f"Error checking trading day for {check_date}: {e}")
        return check_date.weekday() < 5

def get_next_trading_day(check_date: date) -> date:
    """获取下一个交易日"""
    next_day = check_date + timedelta(days=1)
    while not is_trading_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def get_previous_trading_day(check_date: date) -> date:
    """获取上一个交易日"""
    prev_day = check_date - timedelta(days=1)
    while not is_trading_day(prev_day):
        prev_day -= timedelta(days=1)
    return prev_day

def format_number(num: float, decimals: int = 2) -> str:
    """格式化数字显示"""
    if abs(num) >= 100000000:
        return f"{num/100000000:.{decimals}f}亿"
    elif abs(num) >= 10000:
        return f"{num/10000:.{decimals}f}万"
    else:
        return f"{num:.{decimals}f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """格式化百分比显示"""
    return f"{value*100:.{decimals}f}%"

def parse_stock_code(code: str) -> Dict[str, str]:
    """解析股票代码"""
    code = code.strip()
    market = ""

    if code.startswith("6"):
        market = "SH"  # 上交所
    elif code.startswith("0") or code.startswith("3"):
        market = "SZ"  # 深交所
    elif code.startswith("8"):
        market = "BJ"  # 北交所

    return {
        "code": code,
        "market": market
    }

def validate_stock_code(code: str) -> bool:
    """验证股票代码格式"""
    if not code:
        return False

    # A股代码通常为6位数字
    if len(code) != 6:
        return False

    if not code.isdigit():
        return False

    # 检查前缀
    valid_prefixes = ["0", "3", "6", "8"]
    if code[0] not in valid_prefixes:
        return False

    return True

def get_stock_list() -> pd.DataFrame:
    """获取A股股票列表"""
    try:
        stock_info = ak.stock_zh_a_spot_em()
        return stock_info[["代码", "名称"]]
    except Exception as e:
        logger.error(f"Failed to get stock list: {e}")
        return pd.DataFrame()

def batch(iterable, n=1):
    """批量处理函数"""
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法"""
    if denominator == 0:
        return default
    return numerator / denominator

def calculate_days_between(date1: date, date2: date) -> int:
    """计算两个日期之间的天数"""
    return abs((date2 - date1).days)

def get_date_range(start_date: date, end_date: date) -> List[date]:
    """获取日期范围内的所有日期"""
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

def retry(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

def setup_logging(name: str = None) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name or __name__)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """清理DataFrame数据"""
    # 删除全为NaN的行和列
    df = df.dropna(how='all').dropna(axis=1, how='all')

    # 填充剩余的NaN值
    df = df.fillna(0)

    # 重置索引
    df = df.reset_index(drop=True)

    return df

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """验证DataFrame是否包含必需的列"""
    if df.empty:
        return False

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False

    return True