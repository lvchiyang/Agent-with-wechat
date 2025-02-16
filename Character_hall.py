# 用于创建和管理角色，目前只用于将角色拉起来，之后基于此实现更复杂社会群体功能。

from backend.Agent.Agent_class import Agent
import time
import signal
import sys
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def signal_handler(sig, frame, agent):
    print("\nReceived interrupt signal, stopping agent...")
    agent.chat_server.stop()
    logger.info("Services stopped")
    sys.exit(0)

def create_and_run_agent():
    agent = Agent()  # 直接初始化即可
    agent.start()
    
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, agent))
    
    try:
        # 主线程简单循环
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        agent.stop()
        logger.info("Services stopped")

if __name__ == "__main__":  # 底层全部写好，之后可以整体作为后端
    create_and_run_agent()