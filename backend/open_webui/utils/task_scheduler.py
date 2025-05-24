import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import threading

from open_webui.models.subscription import DailyCreditGrants

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器 - 处理每日积分发放等定时任务"""

    def __init__(self):
        self.running = False
        self.scheduler_thread = None

    def start(self):
        """启动任务调度器"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler, daemon=True
            )
            self.scheduler_thread.start()
            logger.info("任务调度器已启动")

    def stop(self):
        """停止任务调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("任务调度器已停止")

    def _run_scheduler(self):
        """运行调度器主循环"""
        last_daily_grant_date = None

        while self.running:
            try:
                current_date = datetime.now().date()

                # 检查是否需要执行每日积分发放（每天执行一次）
                if last_daily_grant_date != current_date:
                    # 在每天的指定时间执行（比如凌晨1点）
                    current_hour = datetime.now().hour
                    if current_hour >= 1:  # 凌晨1点后执行
                        logger.info(f"开始执行每日积分发放任务 - {current_date}")
                        self._execute_daily_credit_grants()
                        last_daily_grant_date = current_date
                        logger.info(f"每日积分发放任务完成 - {current_date}")

                # 每小时检查一次
                time.sleep(3600)

            except Exception as e:
                logger.error(f"任务调度器运行错误: {str(e)}")
                time.sleep(300)  # 发生错误时等待5分钟后重试

    def _execute_daily_credit_grants(self) -> Dict[str, Any]:
        """执行每日积分发放任务"""
        try:
            result = DailyCreditGrants.process_daily_grants_for_all_users()
            logger.info(f"每日积分发放结果: {result}")
            return result
        except Exception as e:
            logger.error(f"每日积分发放失败: {str(e)}")
            return {"success": False, "error": str(e), "message": "每日积分发放失败"}


# 全局任务调度器实例
task_scheduler = TaskScheduler()


def start_task_scheduler():
    """启动任务调度器"""
    task_scheduler.start()


def stop_task_scheduler():
    """停止任务调度器"""
    task_scheduler.stop()


def manual_execute_daily_grants() -> Dict[str, Any]:
    """手动执行每日积分发放"""
    return task_scheduler._execute_daily_credit_grants()
