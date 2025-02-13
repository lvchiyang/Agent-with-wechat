import time
import threading
import logging
from backend.plugins.chat_server import ChatServer
from backend.Memory.memory_manager import MemoryManager
from backend.LLM.LLM_Client import LLM_Client
from backend.LLM.prompt_manager import PromptManager
from backend.Agent.plan import Plan
import asyncio

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
        self.memory = None
        self.LLMClient = LLM_Client()
        self.memory = MemoryManager(self.LLMClient)
        self.prompt_manager = PromptManager()
        self.chat_server = ChatServer()
        self.chat_server.websocket_handler.message_callback = self.handle_message
        self.plan_thread = Plan()   

    def start(self):
        try:
            logger.info("Starting Agent")
            self.plan_thread.start()
            self.chat_server.start()
            logger.info("Agent started successfully")
        except Exception as e:
            logger.error(f"Error starting Agent: {str(e)}")

    def stop(self):
        """停止Agent,停止所有线程"""
        self.chat_server.stop()
        self.plan_thread.stop()

    def handle_message(self, message: str) -> str: # 类当中定义的一个异步接收消息的函数
        # 检查消息是否按照约定的json格式
        context = self.memory.new_message(message)   
        processed = self._process_message(message, context) # 回调函数，虽然是chat_server的函数，但是这就回到Agent里面了。
        # 将上下文信息保存到相关结构体中
        self.memory.add_conversation(message, processed)
        return processed # 这还直接将处理后的消息返回给chat_server，然后chat_server再返回给用户。还直接回去了！

    def _process_message(self, message: str, context: str) -> str:
        # 查询相关记忆
        related_memories = self.memory.query_context(message)
        # 调用LLM或其他处理逻辑
        prompt_manager = self.prompt_manager.get_context_prompt(message, related_memories, context)
        response = self.LLMClient.chat(prompt_manager)
        return f"{response}"
    

        




        




