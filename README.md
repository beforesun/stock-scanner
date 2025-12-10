# A股量化交易筛选系统

基于Docker部署的Web应用，实现A股市场的自动化筛选和交易信号识别。

## 功能特性

- **周末全市场扫描**: 筛选符合长期趋势的股票（收盘价>233周均线 且 周成交量>周MA20）
- **工作日精选池监控**: 从周末筛选结果中找出日线金叉信号（均量线20日金叉60日 且 120分钟MACD红柱放大）
- **买入信号识别**: 识别"缩量旗形+放量中阳"形态，给出具体买入建议和止损位

## 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **语言**: Python 3.11+
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **任务调度**: APScheduler 3.10+

### 前端
- **框架**: Vue 3.3+ (Composition API)
- **UI组件**: Element Plus 2.4+
- **图表**: ECharts 5.4+

### 基础设施
- **容器化**: Docker 24+, Docker Compose 2.20+
- **Web服务器**: Nginx 1.24+

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd stock-scanner
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和Redis连接
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 访问系统

- 前端界面: http://localhost
- API文档: http://localhost:8000/docs

## 项目结构

```
stock-scanner/
├── backend/                    # 后端服务
│   ├── app/                   # 应用代码
│   │   ├── api/              # API路由
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic模型
│   │   ├── services/         # 业务逻辑
│   │   ├── utils/            # 工具函数
│   │   └── scheduler/        # 定时任务
│   ├── requirements.txt      # Python依赖
│   └── Dockerfile            # 后端容器配置
├── frontend/                  # 前端服务
│   ├── src/                  # 前端源码
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 公共组件
│   │   ├── api/              # API接口
│   │   └── stores/           # 状态管理
│   └── Dockerfile            # 前端容器配置
├── sql/                       # 数据库初始化
├── docker-compose.yml        # Docker编排
└── nginx.conf                # Nginx配置
```

## 详细部署

### 环境要求

- Docker 24.0+
- Docker Compose 2.20+
- 至少 8GB 内存（推荐 16GB）
- 100GB 可用磁盘空间

### 1. 环境配置

编辑 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://stock_user:stock_pass@postgres:5432/stock_db

# Redis配置
REDIS_URL=redis://redis:6379/0

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# 任务调度配置
WEEKEND_SCAN_HOUR=20
WEEKEND_SCAN_MINUTE=0
DAILY_SCAN_HOUR=15
DAILY_SCAN_MINUTE=5

# 并行处理配置
MAX_WORKERS=8

# 日志配置
LOG_LEVEL=INFO
```

### 2. 数据初始化

首次启动需要初始化股票列表：

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行初始化脚本
python scripts/init_stock_list.py

# 下载历史数据（可选）
python scripts/download_historical_data.py
```

### 3. 定时任务

系统会自动运行以下定时任务：

- **周末扫描**: 每周日 20:00
- **日筛选**: 工作日 15:05
- **MACD更新**: 工作日 10:30, 13:00, 15:05
- **数据清理**: 每周六 02:00

### 4. 手动操作

通过API可以手动触发扫描：

```bash
# 触发周末扫描
curl -X POST http://localhost:8000/api/v1/weekend-scan/trigger

# 触发日筛选
curl -X POST http://localhost:8000/api/v1/daily-pool/trigger
```

## API文档

### 周末扫描相关

#### 获取最新扫描结果
```http
GET /api/v1/weekend-scan/latest
```

#### 手动触发扫描
```http
POST /api/v1/weekend-scan/trigger
```

#### 获取历史记录
```http
GET /api/v1/weekend-scan/history?page=1&size=20
```

### 日筛选池相关

#### 获取最新筛选池
```http
GET /api/v1/daily-pool/latest
```

#### 手动触发筛选
```http
POST /api/v1/daily-pool/trigger
```

### 交易信号相关

#### 获取最新信号
```http
GET /api/v1/signals/latest?status=PENDING
```

#### 获取信号详情
```http
GET /api/v1/signals/{signal_id}
```

#### 更新信号状态
```http
PUT /api/v1/signals/{signal_id}/status
Content-Type: application/json

{
  "status": "CONFIRMED",
  "note": "已买入"
}
```

### 个股数据相关

#### 获取个股详情
```http
GET /api/v1/stocks/{code}
```

#### 获取K线数据
```http
GET /api/v1/stocks/{code}/klines?type=daily&days=60
```

## 开发指南

### 本地开发

1. 安装Python依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 安装Node.js依赖：
```bash
cd frontend
npm install
```

3. 启动开发服务：
```bash
# 后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run dev
```

### 添加新功能

1. 后端开发：
   - 在 `models/` 添加数据模型
   - 在 `schemas/` 添加Pydantic模型
   - 在 `services/` 添加业务逻辑
   - 在 `api/` 添加API路由

2. 前端开发：
   - 在 `views/` 添加页面组件
   - 在 `components/` 添加公共组件
   - 在 `api/` 添加API接口
   - 在 `stores/` 添加状态管理

### 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "Description"

# 应用迁移
alembic upgrade head
```

## 性能优化

### 1. 数据库优化

- 创建必要的索引
- 使用连接池
- 定期清理旧数据

### 2. Redis缓存

- 缓存热点数据
- 设置合理的TTL
- 使用批量操作

### 3. 并行处理

- 调整 `MAX_WORKERS` 参数
- 使用异步IO
- 优化批量处理

## 监控与日志

### 健康检查

```http
GET /health
```

### 日志查看

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看定时任务日志
docker-compose logs -f scheduler

# 查看所有日志
docker-compose logs -f
```

### 性能监控

- 使用Prometheus + Grafana监控
- 设置告警规则
- 监控关键指标

## 故障排除

### 常见问题

1. **容器启动失败**
   - 检查端口是否被占用
   - 检查环境变量配置
   - 查看容器日志

2. **数据库连接失败**
   - 检查PostgreSQL服务状态
   - 验证连接字符串
   - 检查网络连通性

3. **Redis连接失败**
   - 检查Redis服务状态
   - 验证连接字符串
   - 检查防火墙设置

4. **数据获取失败**
   - 检查AKShare服务状态
   - 验证网络连接
   - 查看API限制

### 调试技巧

1. 启用调试模式：
```bash
DEBUG=True docker-compose up
```

2. 进入容器调试：
```bash
docker-compose exec backend bash
```

3. 使用Python调试器：
```python
import pdb; pdb.set_trace()
```

## 安全建议

1. 修改默认密码
2. 使用HTTPS
3. 限制API访问
4. 定期更新依赖
5. 监控异常访问

## 扩展功能

### 1. 消息推送

集成微信、钉钉或邮件推送：
```python
# 示例：微信推送
async def send_wechat_notification(signal):
    # 实现推送逻辑
    pass
```

### 2. 回测系统

添加策略回测功能：
```python
# 示例：回测引擎
class Backtester:
    async def backtest(self, start_date, end_date):
        # 实现回测逻辑
        pass
```

### 3. 风险管理

添加风险控制模块：
```python
# 示例：风险管理
class RiskManager:
    def check_position_size(self, signal, account_balance):
        # 实现风控逻辑
        pass
```

## 许可证

MIT License

## 技术支持

如有问题，请提交Issue或联系维护团队。

## 更新日志

### v1.0.0 (2024-12-09)
- 初始版本发布
- 实现周末扫描功能
- 实现日筛选功能
- 实现形态识别功能
- 完成前端界面
- 支持Docker部署