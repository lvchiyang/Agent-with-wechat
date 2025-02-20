# 用于创建和管理角色，目前只用于将角色拉起来，之后基于此实现更复杂社会群体功能。

import asyncio
import signal
import sys
import logging
import functools
import lancedb
import numpy as np  # 添加numpy导入



logger = logging.getLogger(__name__)

class AsyncAgent:
    def __init__(self):
        self.stop_event = asyncio.Event()
        self.vector_dim = 1024  # 定义向量维度

    async def generate_random_vector(self):
        """生成随机向量"""
        return np.random.rand(self.vector_dim).tolist()

    async def task1(self):
        """异步任务1：每3秒打印向量信息"""
        while not self.stop_event.is_set():
            vector = await self.generate_random_vector()
            print(f"Task1 生成向量 (长度: {len(vector)}): {vector[:3]}...")  # 显示前3个元素
            await asyncio.sleep(3)

    async def task2(self):
        """异步任务2：每5秒生成新向量"""
        while not self.stop_event.is_set():
            vector = await self.generate_random_vector()
            print(f"Task2 最新向量范数: {np.linalg.norm(vector):.4f}")
            await asyncio.sleep(5)

    async def run_tasks(self):
        """运行所有异步任务"""
        await asyncio.gather(
            self.task1(),
            self.task2()
        )

    def stop(self):
        """停止所有任务"""
        self.stop_event.set()

async def create_and_run_agent():
    agent = AsyncAgent()
    
    # 创建任务
    main_task = asyncio.create_task(agent.run_tasks())
    
    # 处理信号
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(shutdown(agent, main_task))
        )
    
    try:
        await main_task
    except asyncio.CancelledError:
        logger.info("任务被取消")
    finally:
        agent.stop()
        logger.info("清理完成，程序退出")

async def shutdown(agent, main_task):
    """优雅关闭"""
    print("\n收到中断信号，正在停止所有服务...")
    main_task.cancel()
    agent.stop()
    await asyncio.sleep(0.1)  # 给任务一些时间进行清理
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(create_and_run_agent())
    except KeyboardInterrupt:
        pass