#!/usr/bin/env python3
"""
A股量化交易筛选系统 - 演示版本
展示核心功能而不需要完整的环境依赖
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 模拟股票数据
def generate_mock_stock_data():
    """生成模拟股票数据用于演示"""

    # 生成一些模拟股票代码
    stocks = [
        {"code": "600519", "name": "贵州茅台", "market": "SH"},
        {"code": "000858", "name": "五粮液", "market": "SZ"},
        {"code": "000002", "name": "万科A", "market": "SZ"},
        {"code": "600036", "name": "招商银行", "market": "SH"},
        {"code": "000001", "name": "平安银行", "market": "SZ"},
        {"code": "600309", "name": "万华化学", "market": "SH"},
        {"code": "002415", "name": "海康威视", "market": "SZ"},
        {"code": "600887", "name": "伊利股份", "market": "SH"}
    ]

    # 为每只股票生成模拟数据
    all_data = []

    for stock in stocks:
        # 生成一年的日线数据（约250个交易日）
        dates = pd.date_range(end=datetime.now(), periods=250, freq='B')  # 工作日

        # 生成价格数据（随机游走）
        base_price = np.random.uniform(20, 2000)
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        # 生成成交量数据
        volumes = np.random.lognormal(mean=15, sigma=1, size=len(dates)).astype(int)

        # 生成OHLC数据
        for i, date in enumerate(dates):
            close = prices[i]
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_ = np.random.uniform(low, high)

            all_data.append({
                "code": stock["code"],
                "name": stock["name"],
                "date": date.strftime("%Y-%m-%d"),
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": int(volumes[i])
            })

    return pd.DataFrame(all_data)

# 技术指标计算
def calculate_ma(data, period):
    """计算移动平均线"""
    return data.rolling(window=period).mean()

def calculate_macd(close_prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = close_prices.ewm(span=fast).mean()
    ema_slow = close_prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def detect_golden_cross(short_ma, long_ma):
    """检测金叉"""
    if len(short_ma) < 2 or len(long_ma) < 2:
        return False

    # 检查最近是否金叉
    recent_short = short_ma.tail(5)
    recent_long = long_ma.tail(5)

    for i in range(len(recent_short) - 1):
        if (recent_short.iloc[i] <= recent_long.iloc[i] and
            recent_short.iloc[i + 1] > recent_long.iloc[i + 1]):
            return True
    return False

def check_macd_red_bar_increase(macd_hist, days=3):
    """检查MACD红柱连续放大"""
    if len(macd_hist) < days + 1:
        return 0

    consecutive = 0
    for i in range(len(macd_hist) - 1, 0, -1):
        if (macd_hist.iloc[i] > 0 and
            macd_hist.iloc[i] > macd_hist.iloc[i-1]):
            consecutive += 1
        else:
            break

    return consecutive if consecutive >= days else 0

# 周末扫描器
class WeekendScannerDemo:
    """周末扫描器演示版"""

    def __init__(self, df):
        self.df = df
        self.ma_period = 233
        self.vol_ma_period = 20

    def scan_all_stocks(self):
        """扫描所有股票"""
        results = []

        for code in self.df['code'].unique():
            stock_data = self.df[self.df['code'] == code].copy()

            # 计算指标
            stock_data['ma233'] = calculate_ma(stock_data['close'], self.ma_period)
            stock_data['vol_ma20'] = calculate_ma(stock_data['volume'], self.vol_ma_period)

            # 获取最新一周数据
            latest = stock_data.iloc[-1]

            # 判断条件
            pass_condition = (
                latest['close'] > latest['ma233'] and
                latest['volume'] > latest['vol_ma20']
            )

            if pass_condition:
                results.append({
                    'code': code,
                    'name': latest['name'],
                    'close_price': float(latest['close']),
                    'ma233_weekly': float(latest['ma233']),
                    'volume': int(latest['volume']),
                    'vol_ma20_weekly': int(latest['vol_ma20'])
                })

        return {
            'scan_date': datetime.now().strftime('%Y-%m-%d'),
            'total_count': len(self.df['code'].unique()),
            'passed_count': len(results),
            'results': results
        }

# 日筛选器
class DailyScannerDemo:
    """日筛选器演示版"""

    def __init__(self, df):
        self.df = df

    def scan_daily_pool(self, weekend_results):
        """从周末结果中筛选"""
        results = []

        for stock in weekend_results:
            code = stock['code']
            stock_data = self.df[self.df['code'] == code].copy()

            # 检查均量线金叉
            stock_data['vol_ma20'] = calculate_ma(stock_data['volume'], 20)
            stock_data['vol_ma60'] = calculate_ma(stock_data['volume'], 60)

            golden_cross = detect_golden_cross(stock_data['vol_ma20'], stock_data['vol_ma60'])

            if golden_cross:
                # 模拟MACD状态
                macd, macd_signal, macd_hist = calculate_macd(stock_data['close'])
                consecutive = check_macd_red_bar_increase(macd_hist, 2)

                if consecutive > 0:
                    results.append({
                        'code': code,
                        'name': stock['name'],
                        'golden_cross': True,
                        'macd_120min_status': f'红柱连续放大{consecutive}根'
                    })

        return {
            'scan_date': datetime.now().strftime('%Y-%m-%d'),
            'pool_count': len(results),
            'results': results
        }

# 形态识别器
class PatternRecognizerDemo:
    """形态识别器演示版"""

    def __init__(self, df):
        self.df = df

    def recognize_buy_signals(self, daily_pool):
        """识别买入信号"""
        signals = []

        for stock in daily_pool:
            code = stock['code']
            stock_data = self.df[self.df['code'] == code].copy()

            # 模拟找到涨停板（涨幅>9.8%）
            recent_data = stock_data.tail(30)
            limit_up_days = recent_data[recent_data['close'].pct_change() > 0.098]

            if not limit_up_days.empty:
                # 获取最近涨停日期
                limit_up_date = limit_up_days.iloc[-1]['date']
                limit_up_price = limit_up_days.iloc[-1]['close']

                # 模拟今日放量中阳（涨幅5-9%，成交量放大1.8倍）
                today_data = stock_data.iloc[-1]
                yesterday_data = stock_data.iloc[-2]

                price_change = (today_data['close'] - yesterday_data['close']) / yesterday_data['close']
                volume_ratio = today_data['volume'] / yesterday_data['volume']

                if (0.05 <= price_change <= 0.09 and
                    volume_ratio >= 1.8):

                    # 计算回调天数
                    limit_date = datetime.strptime(limit_up_date, '%Y-%m-%d').date()
                    today_date = datetime.strptime(today_data['date'], '%Y-%m-%d').date()
                    pullback_days = (today_date - limit_date).days

                    signals.append({
                        'code': code,
                        'name': stock['name'],
                        'signal_type': 'BUY',
                        'signal_price': float(today_data['close']),
                        'limit_up_date': limit_up_date,
                        'pullback_days': pullback_days,
                        'volume_ratio': round(volume_ratio, 2),
                        'price_change': round(price_change * 100, 2),
                        'upper_shadow': 0.5,  # 模拟值
                        'stop_loss_price': round(limit_up_price * 0.90, 2),
                        'stop_loss_reason': '涨停板中枢',
                        'reason': f'涨停板后回调{pullback_days}天形成缩量旗形，今日放量{round(volume_ratio, 1)}倍，收涨{round(price_change*100, 1)}%的中阳线'
                    })

        return signals

# 演示主函数
def main():
    """系统演示"""
    print("=" * 60)
    print("A股量化交易筛选系统 - 演示版")
    print("=" * 60)

    # 生成模拟数据
    print("\n1. 生成模拟股票数据...")
    df = generate_mock_stock_data()
    print(f"生成了 {len(df)} 条记录")

    # 周末扫描
    print("\n2. 执行周末扫描...")
    weekend_scanner = WeekendScannerDemo(df)
    weekend_results = weekend_scanner.scan_all_stocks()

    print(f"扫描日期: {weekend_results['scan_date']}")
    print(f"扫描总数: {weekend_results['total_count']}")
    print(f"通过数量: {weekend_results['passed_count']}")
    print("\n通过筛选的股票:")
    for stock in weekend_results['results']:
        print(f"  {stock['code']} {stock['name']} - 收盘价: ¥{stock['close_price']}, 233周均线: ¥{stock['ma233_weekly']}")

    # 日筛选
    print("\n3. 执行日筛选...")
    daily_scanner = DailyScannerDemo(df)
    daily_results = daily_scanner.scan_daily_pool(weekend_results['results'])

    print(f"筛选日期: {daily_results['scan_date']}")
    print(f"入选数量: {daily_results['pool_count']}")
    print("\n入选日筛选池的股票:")
    for stock in daily_results['results']:
        print(f"  {stock['code']} {stock['name']} - 均量线金叉: {stock['golden_cross']}, {stock['macd_120min_status']}")

    # 形态识别
    print("\n4. 识别买入信号...")
    pattern_recognizer = PatternRecognizerDemo(df)
    signals = pattern_recognizer.recognize_buy_signals(daily_results['results'])

    print(f"生成信号数量: {len(signals)}")
    print("\n买入信号:")
    for signal in signals:
        print(f"\n  股票: {signal['code']} {signal['name']}")
        print(f"  信号价格: ¥{signal['signal_price']}")
        print(f"  涨停日期: {signal['limit_up_date']}")
        print(f"  回调天数: {signal['pullback_days']}天")
        print(f"  放量倍数: {signal['volume_ratio']}倍")
        print(f"  涨幅: {signal['price_change']}%")
        print(f"  止损价: ¥{signal['stop_loss_price']}")
        print(f"  理由: {signal['reason']}")

    # 保存结果到文件
    print("\n5. 保存结果到文件...")
    result = {
        "weekend_scan": weekend_results,
        "daily_pool": daily_results,
        "buy_signals": signals
    }

    with open("demo_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("结果已保存到 demo_results.json")
    print("\n演示完成！")

if __name__ == "__main__":
    main()