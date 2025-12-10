-- 1. 股票基础信息表
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    market VARCHAR(10),  -- 'SH' or 'SZ'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 周线数据表
CREATE TABLE IF NOT EXISTS weekly_klines (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    ma233 DECIMAL(10,2),  -- 233周均线
    vol_ma20 BIGINT,      -- 周成交量MA20
    UNIQUE(stock_code, trade_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 3. 日线数据表
CREATE TABLE IF NOT EXISTS daily_klines (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    vol_ma20 BIGINT,      -- 20日均量
    vol_ma60 BIGINT,      -- 60日均量
    UNIQUE(stock_code, trade_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 4. 120分钟K线数据表
CREATE TABLE IF NOT EXISTS kline_120min (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    datetime TIMESTAMP NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    macd DECIMAL(10,4),
    macd_signal DECIMAL(10,4),
    macd_hist DECIMAL(10,4),  -- 红绿柱
    UNIQUE(stock_code, datetime),
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 5. 周末扫描结果表
CREATE TABLE IF NOT EXISTS weekend_scan_results (
    id SERIAL PRIMARY KEY,
    scan_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    close_price DECIMAL(10,2),
    ma233_weekly DECIMAL(10,2),
    volume BIGINT,
    vol_ma20_weekly BIGINT,
    pass_condition BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 6. 日筛选池表
CREATE TABLE IF NOT EXISTS daily_pool (
    id SERIAL PRIMARY KEY,
    scan_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    vol_ma20 BIGINT,
    vol_ma60 BIGINT,
    golden_cross BOOLEAN,  -- 均量线金叉
    macd_120min_status VARCHAR(50),  -- MACD红柱状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 7. 涨停板记录表
CREATE TABLE IF NOT EXISTS limit_up_records (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    limit_date DATE NOT NULL,
    limit_price DECIMAL(10,2),
    volume BIGINT,
    UNIQUE(stock_code, limit_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 8. 交易信号表
CREATE TABLE IF NOT EXISTS trade_signals (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    signal_type VARCHAR(20) NOT NULL,  -- 'BUY', 'SELL'
    signal_date DATE NOT NULL,
    signal_price DECIMAL(10,2),

    -- 买入信号相关字段
    limit_up_date DATE,           -- 涨停板日期
    pullback_days INT,            -- 回调天数
    volume_ratio DECIMAL(5,2),    -- 放量倍数
    price_change DECIMAL(5,2),    -- 涨幅
    upper_shadow DECIMAL(5,2),    -- 上影线占比

    -- 止损价格
    stop_loss_price DECIMAL(10,2),
    stop_loss_reason VARCHAR(100),

    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, CONFIRMED, INVALID
    reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_weekend_scan_date ON weekend_scan_results(scan_date);
CREATE INDEX IF NOT EXISTS idx_daily_pool_date ON daily_pool(scan_date);
CREATE INDEX IF NOT EXISTS idx_signals_date ON trade_signals(signal_date);
CREATE INDEX IF NOT EXISTS idx_signals_status ON trade_signals(status);
CREATE INDEX IF NOT EXISTS idx_weekly_klines_date ON weekly_klines(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_klines_date ON daily_klines(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_120min_datetime ON kline_120min(stock_code, datetime);
CREATE INDEX IF NOT EXISTS idx_stocks_code ON stocks(code);

-- 创建更新时间的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为stocks表创建更新时间触发器
DROP TRIGGER IF EXISTS update_stocks_updated_at ON stocks;
CREATE TRIGGER update_stocks_updated_at
    BEFORE UPDATE ON stocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入测试数据
INSERT INTO stocks (code, name, market) VALUES
    ('600519', '贵州茅台', 'SH'),
    ('000858', '五粮液', 'SZ'),
    ('000002', '万科A', 'SZ'),
    ('600036', '招商银行', 'SH'),
    ('000001', '平安银行', 'SZ')
ON CONFLICT (code) DO NOTHING;