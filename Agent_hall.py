from backend.Agent.Agent_class import Agent
import time
import signal
import sys
import logging
import threading

logger = logging.getLogger(__name__)

def signal_handler(sig, frame, agent_thread):
    print("\n收到中断信号，正在停止所有服务...")
    agent_thread.stop()
    logger.info("服务已完全停止")
    exit(0)

def Agent_hall(): # 主进程
    agent_thread = Agent()
    agent_thread.start()
    
    # 注册信号处理
    signals = (signal.SIGINT, signal.SIGTERM)
    for s in signals:
        signal.signal(s, lambda sig, frame: signal_handler(sig, frame, agent_thread))
    
    agent_thread.join()


if __name__ == "__main__":
    Agent_hall()



