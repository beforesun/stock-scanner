from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from datetime import datetime
from dotenv import load_dotenv

from app.database import engine, Base
from app.api import weekend_scan, daily_pool, signals, stocks
from app.scheduler.jobs import setup_scheduler

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 启动定时任务
    setup_scheduler()

    yield

    # 关闭时清理资源
    await engine.dispose()

app = FastAPI(
    title="A股量化交易筛选系统",
    description="基于均量线和MACD指标的A股量化交易筛选系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(weekend_scan.router, prefix="/api/v1/weekend-scan", tags=["周末扫描"])
app.include_router(daily_pool.router, prefix="/api/v1/daily-pool", tags=["日筛选池"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["交易信号"])
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["个股数据"])

@app.get("/")
async def root():
    return {"message": "A股量化交易筛选系统 API"}

@app.get("/health")
async def health_check():
    from app.database import check_db_connection
    from app.utils.redis_client import check_redis_connection

    db_status = await check_db_connection()
    redis_status = await check_redis_connection()

    return {
        "status": "healthy" if db_status and redis_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": datetime.now().isoformat()
    }