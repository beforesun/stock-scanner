#!/usr/bin/env python3
"""
A股量化交易筛选系统 - 简化演示
无需外部依赖的纯Python演示
"""

from datetime import datetime, timedelta
import json
import random

class Stock:
    def __init__(self, code, name, market):
        self.code = code
        self.name = name
        self.market = market
        self.prices = []
        self.volumes = []

    def generate_data(self, days=250):
        """生成模拟数据"""
        base_price = random.uniform(20, 2000)
        price = base_price

        for i in range(days):
            # 模拟价格变动（-5% 到 +5%）
            change = random.uniform(-0.05, 0.05)
            price = price * (1 + change)

            # 生成OHLC
            high = price * (1 + random.uniform(0, 0.02))
            low = price * (1 - random.uniform(0, 0.02))
            open_price = random.uniform(low, high)

            # 成交量（100万到1亿）
            volume = random.randint(1000000, 100000000)

            date = datetime.now() - timedelta(days=days-i)

            self.prices.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(price, 2),
                'volume': volume
            })

def calculate_ma(data, period):
    """计算移动平均"""
    if len(data) < period:
        return None
    return sum(data[-period:]) / period

def weekend_scan(stocks):
    """周末扫描 - 筛选收盘价>233周均线且周成交量>周MA20"""
    print("\n🔍 执行周末扫描...")
    results = []

    for stock in stocks:
        # 简化为使用日线数据模拟周线
        recent_data = stock.prices[-20:]  # 最近20天作为模拟

        if len(recent_data) < 20:
            continue

        # 计算233日移动平均（模拟233周均线）
        closes = [p['close'] for p in stock.prices]
        ma233 = calculate_ma(closes, 233)

        if not ma233:
            continue

        # 最新收盘价
        latest_close = recent_data[-1]['close']
        latest_volume = recent_data[-1]['volume']

        # 计算20日成交量移动平均（模拟周MA20）
        volumes = [p['volume'] for p in recent_data]
        vol_ma20 = calculate_ma(volumes, 20)

        # 检查条件
        if latest_close > ma233 and latest_volume > vol_ma20:
            results.append({
                'code': stock.code,
                'name': stock.name,
                'close_price': latest_close,
                'ma233_weekly': ma233,
                'volume': latest_volume,
                'vol_ma20_weekly': vol_ma20
            })

    return {
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'total_count': len(stocks),
        'passed_count': len(results),
        'results': results
    }

def daily_scan(weekend_results, stocks_dict):
    """日筛选 - 从周末结果中筛选均量线金叉和MACD红柱放大"""
    print("\n📊 执行日筛选...")
    results = []

    for stock_info in weekend_results['results']:
        stock = stocks_dict[stock_info['code']]

        # 获取最近30天数据
        recent_data = stock.prices[-30:]

        # 计算20日和60日均量线
        volumes = [p['volume'] for p in recent_data]
        vol_ma20 = calculate_ma(volumes, 20)
        vol_ma60 = calculate_ma(volumes, 60)

        # 检查金叉（简化版）
        if vol_ma20 and vol_ma60 and vol_ma20 > vol_ma60:
            # 模拟MACD红柱放大
            results.append({
                'code': stock.code,
                'name': stock.name,
                'vol_ma20': vol_ma20,
                'vol_ma60': vol_ma60,
                'golden_cross': True,
                'macd_120min_status': '红柱连续放大3根'
            })

    return {
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'pool_count': len(results),
        'results': results
    }

def pattern_recognition(daily_results, stocks_dict):
    """形态识别 - 识别缩量旗形+放量中阳"""
    print("\n🎯 识别买入信号...")
    signals = []

    for stock_info in daily_results['results']:
        stock = stocks_dict[stock_info['code']]

        # 获取最近10天数据
        recent_data = stock.prices[-10:]

        # 模拟找到涨停板（涨幅>9.8%）
        limit_up_day = None
        for i, day in enumerate(recent_data[:-1]):
            prev_close = recent_data[i-1]['close'] if i > 0 else day['open']
            change = (day['close'] - prev_close) / prev_close
            if change > 0.098:
                limit_up_day = day
                limit_up_index = i
                break

        if limit_up_day:
            # 检查今日是否为放量中阳
            today = recent_data[-1]
            yesterday = recent_data[-2]

            price_change = (today['close'] - yesterday['close']) / yesterday['close']
            volume_ratio = today['volume'] / yesterday['volume']

            # 放量中阳条件
            if 0.05 <= price_change <= 0.09 and volume_ratio >= 1.8:
                # 计算回调天数
                limit_date = datetime.strptime(limit_up_day['date'], '%Y-%m-%d').date()
                today_date = datetime.strptime(today['date'], '%Y-%m-%d').date()
                pullback_days = (today_date - limit_date).days

                signals.append({
                    'code': stock.code,
                    'name': stock.name,
                    'signal_type': 'BUY',
                    'signal_price': today['close'],
                    'limit_up_date': limit_up_day['date'],
                    'pullback_days': pullback_days,
                    'volume_ratio': round(volume_ratio, 2),
                    'price_change': round(price_change * 100, 2),
                    'upper_shadow': 0.8,
                    'stop_loss_price': round(limit_up_day['close'] * 0.90, 2),
                    'reason': f'涨停板后回调{pullback_days}天形成缩量旗形，今日放量{round(volume_ratio, 1)}倍，收涨{round(price_change*100, 1)}%的中阳线'
                })

    return signals

def main():
    """主函数"""
    print("=" * 60)
    print("A股量化交易筛选系统 - 简化演示")
    print("=" * 60)

    # 创建模拟股票
    print("\n📝 创建模拟股票数据...")
    stocks = [
        Stock("600519", "贵州茅台", "SH"),
        Stock("000858", "五粮液", "SZ"),
        Stock("000002", "万科A", "SZ"),
        Stock("600036", "招商银行", "SH"),
        Stock("000001", "平安银行", "SZ"),
        Stock("600309", "万华化学", "SH"),
        Stock("002415", "海康威视", "SZ"),
        Stock("600887", "伊利股份", "SH")
    ]

    # 生成数据
    for stock in stocks:
        stock.generate_data(250)

    stocks_dict = {stock.code: stock for stock in stocks}

    print(f"创建了 {len(stocks)} 只股票的模拟数据")

    # 执行周末扫描
    weekend_results = weekend_scan(stocks)

    print(f"\n📅 扫描日期: {weekend_results['scan_date']}")
    print(f"📈 扫描总数: {weekend_results['total_count']}")
    print(f"✅ 通过数量: {weekend_results['passed_count']}")

    if weekend_results['passed_count'] > 0:
        print("\n通过筛选的股票:")
        for stock in weekend_results['results']:
            print(f"  📊 {stock['code']} {stock['name']}")
            print(f"     收盘价: ¥{stock['close_price']}, 233周均线: ¥{stock['ma233_weekly']}")
            print(f"     成交量: {stock['volume']:,}, 周MA20: {stock['vol_ma20_weekly']:,}")

    # 执行日筛选
    if weekend_results['passed_count'] > 0:
        daily_results = daily_scan(weekend_results, stocks_dict)

        print(f"\n📅 筛选日期: {daily_results['scan_date']}")
        print(f"✅ 入选数量: {daily_results['pool_count']}")

        if daily_results['pool_count'] > 0:
            print("\n入选日筛选池的股票:")
            for stock in daily_results['results']:
                print(f"  📈 {stock['code']} {stock['name']}")
                print(f"     均量线金叉: {stock['golden_cross']}")
                print(f"     20日均量: {stock['vol_ma20']:,.0f}, 60日均量: {stock['vol_ma60']:,.0f}")
                print(f"     {stock['macd_120min_status']}")
    else:
        daily_results = {'results': []}

    # 识别买入信号
    if daily_results['pool_count'] > 0:
        signals = pattern_recognition(daily_results, stocks_dict)

        print(f"\n🎯 生成信号数量: {len(signals)}")

        if signals:
            print("\n🚀 买入信号:")
            for i, signal in enumerate(signals, 1):
                print(f"\n  📋 信号 #{i}: {signal['code']} {signal['name']}")
                print(f"     💰 信号价格: ¥{signal['signal_price']}")
                print(f"     📅 涨停日期: {signal['limit_up_date']}")
                print(f"     ⏰ 回调天数: {signal['pullback_days']}天")
                print(f"     📊 放量倍数: {signal['volume_ratio']}倍")
                print(f"     📈 涨幅: {signal['price_change']}%")
                print(f"     🛑 止损价: ¥{signal['stop_loss_price']}")
                print(f"     💡 理由: {signal['reason']}")
    else:
        signals = []

    # 保存结果
    print("\n💾 保存结果到文件...")
    result = {
        "weekend_scan": weekend_results,
        "daily_pool": daily_results,
        "buy_signals": signals,
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    with open("demo_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("✅ 结果已保存到 demo_results.json")
    print("\n🎉 演示完成！")

    # 显示统计信息
    print(f"\n📊 统计汇总:")
    print(f"   总股票数: {len(stocks)}")
    print(f"   周末筛选通过: {weekend_results['passed_count']}")
    print(f"   日筛选入选: {daily_results['pool_count']}")
    print(f"   买入信号: {len(signals)}")

if __name__ == "__main__":
    main()