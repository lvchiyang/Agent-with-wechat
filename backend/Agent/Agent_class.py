import time
import threading
import logging
from backend.plugins.chat_server import ChatServer
from backend.Memory.memory_manager import MemoryManager
from backend.LLM.LLM_Client import LLM_Client
from backend.LLM.prompt_manager import PromptManager
from backend.Agent.plan import Plan
import asyncio  
from typing import List, Dict
'''
# Agent需要的变量：

当前状态/正在做的事情
个人信息
上下文；
记忆的保存路径；
在初始化时候，开启规划的线程

'''

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent():
    def __init__(self):
        self.LLMClient = LLM_Client()
        self.memory = MemoryManager(self.LLMClient)
        self.prompt_manager = PromptManager()
        self.chat_server = ChatServer()
        self.chat_server.websocket_handler.message_callback = self.handle_message
        self.current_state = "idle"  # 添加当前状态
        # 传递memory实例给Plan
        self.plan_thread = Plan(
            state_callback=self.update_state, # 状态更新回调
            memory_manager=self.memory, # 传递memory实例，用于调用每日信息总结
            llm_client=self.LLMClient # 传递llm实例，用于调用llm_plan
        )

    def start(self):
        try:
            logger.info("Starting Agent")
            # 先启动WebSocket服务器
            self.chat_server.start()
            # 再启动计划线程
            self.plan_thread.start()
            logger.info("Agent started successfully")
        except Exception as e:
            logger.error(f"Error starting Agent: {str(e)}")
            self.stop()

    def stop(self):
        """停止Agent,停止所有线程"""
        self.chat_server.stop()
        self.plan_thread.stop()

    async def handle_message(self, message: dict) -> str:   
        # 提供上下文
        context = self.memory.new_message(message)
        related_memories = self.memory.query_context(message)
        prompt_manager = self.prompt_manager.get_system_prompt(message, related_memories, context, self.current_state)

        response = await self.llm_client.chat(system_prompt = prompt_manager, user_input = message, enable_search=True)
        self.memory.add_conversation(),
        
        return response

    def update_state(self, new_state: str):
        """更新Agent状态"""
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"Agent状态更新: {old_state} -> {new_state}")
        # 这里可以添加状态变化时的其他处理逻辑










