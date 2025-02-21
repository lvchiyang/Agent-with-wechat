import asyncio
import logging

logger = logging.getLogger(__name__)


async def work():
    print(f"正在工作")
    # 模拟耗时任务
    await asyncio.sleep(3600) # ← 这里也会释放GIL
    print(f"工作结束") 