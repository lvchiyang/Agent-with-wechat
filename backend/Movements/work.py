import threading
import time
import logging

logger = logging.getLogger(__name__)


def work():
    print(f"正在工作")
    # 模拟耗时任务
    time.sleep(10) # ← 这里也会释放GIL
    print(f"工作结束") 