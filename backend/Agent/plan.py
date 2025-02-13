import threading
import time
import logging
from backend.Movements import hobby, relax, work
from backend.LLM.LLM_Client import LLM_Client
from backend.LLM.prompt_manager import PromptManager
import asyncio
'''
plan作为一个任务管理线程存在，暂时不需要事件循环，实现响应接口，将其注释掉；
Movements下是可以执行的任务空间，每个任务是一个同步函数，plan等待每一个任务的完成，
每次调用llm，询问要执行的任务，返回要执行的任务名称，在plan中完成对llm返回的信息的解析，调用movements中的任务函数，
'''

logger = logging.getLogger(__name__)


class Plan():
    def __init__(self):
        self.should_continue = True  # 控制循环的变量
        self.plan_thread = threading.Thread(target=self._plan_loop)
        self.plan_thread.daemon = True

    def start(self):
        """启动计划线程"""
        if not self.plan_thread.is_alive():
            self.plan_thread.start()
            logger.info("Plan thread started")

    def stop(self):
        """停止计划线程"""
        self.should_continue = False
        if self.plan_thread.is_alive():
            self.plan_thread.join(timeout=5)  # 等待线程结束
            if self.plan_thread.is_alive():  # 这里还是有问题
                logger.warning("Plan thread did not stop gracefully")
            else:
                logger.info("Plan thread stopped successfully")

    async def _plan_loop(self):
        """计划执行的主循环"""
        while self.should_continue:
            try:
                # 示例任务调度逻辑
                logger.info("执行日常计划...")
                work.do_work()
                time.sleep(5)
                hobby.practice_hobby()
                time.sleep(5)
                relax.take_break()
                
            except Exception as e:
                logger.error(f"计划执行出错: {str(e)}")
            time.sleep(60)  # 每分钟检查一次任务



