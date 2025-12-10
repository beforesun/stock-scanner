from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging
import os
from datetime import datetime

from app.services.signal_generator import SignalGenerator
from app.utils.helpers import is_trading_day

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler(
    job_defaults={
        'max_instances': 1,
        'coalesce': True,
        'misfire_grace_time': 300
    }
)

signal_generator = SignalGenerator()

async def weekend_scan_job():
    """周末全市场扫描任务"""
    logger.info("Starting weekend scan job...")

    try:
        # 检查是否应该运行
        if not await signal_generator.should_run_weekend_scan():
            logger.info("Weekend scan already completed today, skipping...")
            return

        # 执行扫描
        result = await signal_generator.generate_weekend_signals()

        logger.info(f"Weekend scan completed: {result['passed_count']} stocks passed")

    except Exception as e:
        logger.error(f"Weekend scan job failed: {e}")

async def daily_scan_job():
    """工作日筛选任务"""
    logger.info("Starting daily scan job...")

    try:
        # 检查是否应该运行
        if not await signal_generator.should_run_daily_scan():
            logger.info("Daily scan not needed or already completed, skipping...")
            return

        # 执行日筛选
        result = await signal_generator.generate_daily_signals()

        logger.info(f"Daily scan completed: {result['signal_count']} signals generated")

    except Exception as e:
        logger.error(f"Daily scan job failed: {e}")

async def update_120min_macd_job():
    """更新120分钟MACD数据"""
    logger.info("Updating 120min MACD data...")

    try:
        await signal_generator.update_realtime_data()
        logger.info("120min MACD update completed")

    except Exception as e:
        logger.error(f"120min MACD update failed: {e}")

async def daily_data_update_job():
    """每日数据更新任务"""
    logger.info("Starting daily data update...")

    try:
        # 如果不是交易日，跳过
        if not is_trading_day(datetime.now().date()):
            logger.info("Not a trading day, skipping daily data update")
            return

        # 这里可以添加数据更新逻辑
        # 例如：更新日线数据、计算指标等

        logger.info("Daily data update completed")

    except Exception as e:
        logger.error(f"Daily data update failed: {e}")

async def cleanup_old_data_job():
    """清理旧数据任务"""
    logger.info("Starting cleanup old data...")

    try:
        # 清理1年前的120分钟数据
        # 清理6个月前的日线数据
        # 清理3个月前的信号数据（已确认或作废的）

        logger.info("Cleanup old data completed")

    except Exception as e:
        logger.error(f"Cleanup old data failed: {e}")

# 配置定时任务
def setup_scheduler():
    """配置并启动定时任务"""

    # 周末扫描: 每周日 20:00
    scheduler.add_job(
        weekend_scan_job,
        CronTrigger(
            day_of_week='sun',
            hour=int(os.getenv('WEEKEND_SCAN_HOUR', '20')),
            minute=int(os.getenv('WEEKEND_SCAN_MINUTE', '0'))
        ),
        id='weekend_scan',
        name='Weekend Market Scan'
    )

    # 工作日筛选: 周一到周五 15:05
    scheduler.add_job(
        daily_scan_job,
        CronTrigger(
            day_of_week='mon-fri',
            hour=int(os.getenv('DAILY_SCAN_HOUR', '15')),
            minute=int(os.getenv('DAILY_SCAN_MINUTE', '5'))
        ),
        id='daily_scan',
        name='Daily Stock Pool Scan'
    )

    # 120分钟MACD更新: 周一到周五 10:30, 13:00, 15:05
    scheduler.add_job(
        update_120min_macd_job,
        CronTrigger(
            day_of_week='mon-fri',
            hour='10,13,15',
            minute='30,0,5'
        ),
        id='update_120min_macd',
        name='Update 120min MACD'
    )

    # 每日数据更新: 周一到周五 16:00
    scheduler.add_job(
        daily_data_update_job,
        CronTrigger(
            day_of_week='mon-fri',
            hour=16,
            minute=0
        ),
        id='daily_data_update',
        name='Daily Data Update'
    )

    # 清理旧数据: 每周六 02:00
    scheduler.add_job(
        cleanup_old_data_job,
        CronTrigger(
            day_of_week='sat',
            hour=2,
            minute=0
        ),
        id='cleanup_old_data',
        name='Cleanup Old Data'
    )

    # 启动调度器
    scheduler.start()
    logger.info("Scheduler started with jobs:")

    # 打印所有任务
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: {job.trigger}")

def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")

# 获取调度器状态
def get_scheduler_status():
    """获取调度器状态"""
    if not scheduler.running:
        return {
            'status': 'stopped',
            'jobs': []
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })

    return {
        'status': 'running',
        'jobs': jobs
    }