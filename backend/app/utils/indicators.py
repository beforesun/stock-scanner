import pandas as pd
import numpy as np
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_ma(data: pd.Series, period: int) -> pd.Series:
    """计算移动平均线"""
    return data.rolling(window=period, min_periods=1).mean()

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """计算指数移动平均线"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """计算MACD指标

    Returns:
        DataFrame with columns: macd, macd_signal, macd_hist
    """
    # 计算EMA
    ema_fast = calculate_ema(data, fast_period)
    ema_slow = calculate_ema(data, slow_period)

    # 计算MACD线
    macd = ema_fast - ema_slow

    # 计算信号线
    macd_signal = calculate_ema(macd, signal_period)

    # 计算柱状图
    macd_hist = macd - macd_signal

    return pd.DataFrame({
        'macd': macd,
        'macd_signal': macd_signal,
        'macd_hist': macd_hist
    })

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """计算RSI相对强弱指标"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def calculate_bollinger_bands(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:
    """计算布林带"""
    middle_band = calculate_ma(data, period)
    std = data.rolling(window=period).std()

    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)

    return pd.DataFrame({
        'middle': middle_band,
        'upper': upper_band,
        'lower': lower_band
    })

def calculate_volatility(data: pd.Series, period: int = 20) -> pd.Series:
    """计算波动率（标准差）"""
    return data.rolling(window=period).std()

def calculate_volume_ma(volume: pd.Series, period: int) -> pd.Series:
    """计算成交量均线"""
    return volume.rolling(window=period, min_periods=1).mean()

def detect_golden_cross(
    short_ma: pd.Series,
    long_ma: pd.Series,
    days_back: int = 5
) -> bool:
    """检测均线金叉

    Args:
        short_ma: 短期均线
        long_ma: 长期均线
        days_back: 检查最近N天

    Returns:
        True if golden cross detected
    """
    if len(short_ma) < days_back + 1 or len(long_ma) < days_back + 1:
        return False

    # 获取最近N+1天的数据
    recent_short = short_ma.tail(days_back + 1)
    recent_long = long_ma.tail(days_back + 1)

    # 检查是否有金叉
    for i in range(days_back):
        if (recent_short.iloc[i] <= recent_long.iloc[i] and
            recent_short.iloc[i + 1] > recent_long.iloc[i + 1]):
            return True

    return False

def detect_death_cross(
    short_ma: pd.Series,
    long_ma: pd.Series,
    days_back: int = 5
) -> bool:
    """检测均线死叉"""
    if len(short_ma) < days_back + 1 or len(long_ma) < days_back + 1:
        return False

    # 获取最近N+1天的数据
    recent_short = short_ma.tail(days_back + 1)
    recent_long = long_ma.tail(days_back + 1)

    # 检查是否有死叉
    for i in range(days_back):
        if (recent_short.iloc[i] >= recent_long.iloc[i] and
            recent_short.iloc[i + 1] < recent_long.iloc[i + 1]):
            return True

    return False

def check_macd_red_bar_increase(macd_hist: pd.Series, days: int = 3) -> int:
    """检查MACD红柱是否连续放大

    Returns:
        连续放大的天数，0表示未连续放大
    """
    if len(macd_hist) < days + 1:
        return 0

    consecutive = 0
    # 从最新数据开始往前检查
    for i in range(len(macd_hist) - 1, 0, -1):
        if (macd_hist.iloc[i] > 0 and  # 当前是红柱
            macd_hist.iloc[i] > macd_hist.iloc[i-1]):  # 比前一根大
            consecutive += 1
        else:
            break

    return consecutive if consecutive >= days else 0

def calculate_price_change(current: float, previous: float) -> float:
    """计算价格涨跌幅"""
    if previous == 0:
        return 0
    return (current - previous) / previous

def calculate_upper_shadow(open_price: float, high_price: float, close_price: float) -> float:
    """计算上影线占比"""
    if high_price == open_price:
        return 0
    return (high_price - max(open_price, close_price)) / open_price

def calculate_lower_shadow(open_price: float, low_price: float, close_price: float) -> float:
    """计算下影线占比"""
    if open_price == low_price:
        return 0
    return (min(open_price, close_price) - low_price) / open_price

def is_limit_up(
    open_price: float,
    close_price: float,
    previous_close: float,
    threshold: float = 0.098
) -> bool:
    """判断是否涨停（考虑误差）"""
    if previous_close == 0:
        return False

    price_change = (close_price - previous_close) / previous_close
    return price_change >= threshold

def is_limit_down(
    open_price: float,
    close_price: float,
    previous_close: float,
    threshold: float = 0.098
) -> bool:
    """判断是否跌停（考虑误差）"""
    if previous_close == 0:
        return False

    price_change = (close_price - previous_close) / previous_close
    return price_change <= -threshold