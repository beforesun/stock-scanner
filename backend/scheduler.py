#!/usr/bin/env python3
"""
独立的定时任务调度服务
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.scheduler.jobs import setup_scheduler, shutdown_scheduler
from app.utils.helpers import setup_logging

# 设置日志
logger = setup_logging('scheduler')

async def main():
    """主函数"""
    logger.info("Starting stock scanner scheduler service...")

    try:
        # 设置定时任务
        setup_scheduler()

        # 保持服务运行
        logger.info("Scheduler service is running. Press Ctrl+C to stop.")

        # 创建一个事件来保持程序运行
        stop_event = asyncio.Event()

        # 设置信号处理
        def signal_handler():
            logger.info("Received stop signal, shutting down...")
            stop_event.set()

        try:
            # 在Windows上使用不同的信号处理方式
            if sys.platform == 'win32':
                # Windows 使用键盘中断
                while not stop_event.is_set():
                    await asyncio.sleep(1)
            else:
                # Unix-like 系统使用信号
                import signal
                signal.signal(signal.SIGINT, lambda s, f: signal_handler())
                signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

                await stop_event.wait()

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            signal_handler()

    except Exception as e:
        logger.error(f"Scheduler service error: {e}")
        raise

    finally:
        # 关闭调度器
        shutdown_scheduler()
        logger.info("Scheduler service stopped.")

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())