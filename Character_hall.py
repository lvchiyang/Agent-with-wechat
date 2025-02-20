# 用于创建和管理角色，目前只用于将角色拉起来，之后基于此实现更复杂社会群体功能。

from backend.Agent.Agent_class import Agent
import time
import signal
import sys
from pathlib import Path
import logging
import threading

logger = logging.getLogger(__name__)

class AgentThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.agent = Agent()
        self.stop_event = threading.Event()

    def run(self):
        self.agent.start()
        while not self.stop_event.is_set():
            time.sleep(1)  # 适度降低CPU占用

    def stop(self):
        self.stop_event.set()
        self.agent.stop()
        self.join()  # 等待线程结束

def signal_handler(sig, frame, agent_thread):
    print("\n收到中断信号，正在停止所有服务...")
    agent_thread.stop()
    logger.info("服务已完全停止")
    sys.exit(0)

def create_and_run_agent():
    agent_thread = AgentThread()
    agent_thread.start()
    
    # 注册信号处理
    signals = (signal.SIGINT, signal.SIGTERM)
    for s in signals:
        signal.signal(s, lambda sig, frame: signal_handler(sig, frame, agent_thread))
    
    try:
        # 主线程保持运行直到收到信号
        while agent_thread.is_alive():
            agent_thread.join(1)
    except KeyboardInterrupt:
        pass
    finally:
        agent_thread.stop()
        logger.info("清理完成，程序退出")

if __name__ == "__main__":  # 底层全部写好，之后可以整体作为后端
    create_and_run_agent()