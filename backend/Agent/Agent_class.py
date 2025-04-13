import logging
import sys
from backend.channel.chat_server import ChatServer
from backend.Memory.memory_manager import MemoryManager
from backend.LLM.LLM_Client import LLM_Client
from backend.LLM.prompt_manager import PromptManager
from backend.Agent.plan import Plan
import asyncio
import threading
from backend.channel.api_server import APIServer
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


class Agent(threading.Thread):
    def __init__(self):
        super().__init__()  # 调用父类的 __init__ 方法
        self.LLM_Client = LLM_Client()
        self.memory_manager = MemoryManager(self.LLM_Client)
        self.prompt_manager = PromptManager()
        self.new_message = asyncio.Event()  
        # self.chat_server = ChatServer(self.handle_message,self.new_message)
        self.current_state = "idle"  # 添加当前状态
        self.plan = Plan(self.update_state, self.memory_manager, self.LLM_Client) # 传递memory实例给Plan


    async def _run_server_in_thread(self):
        """
        在后台线程中运行服务器
        """
        self.api_server = APIServer(self.handle_message, self.new_message)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.api_server.run_server)

    async def main_loop(self):  # 主事件循环
        await asyncio.gather(
            self._run_server_in_thread(),
            self.plan.plan_loop()
        )

    def run(self):
        try:
            # logger.info("正在创建 Agent")
            # 创建事件循环并运行异步任务
            asyncio.run(self.main_loop())
        except Exception as e:
            logger.error(f"Error starting Agent: {str(e)}")
            self.stop()


    async def handle_message(self, message: dict) -> str:  
        # 提供上下文
        context = self.memory_manager.new_message(message) 
        related_memories = self.memory_manager.query_context(message)
        system_prompt = self.prompt_manager.get_system_prompt(related_memories, context, self.current_state)        
        user_prompt = self.prompt_manager.get_user_prompt(message)        
        response = await self.LLM_Client.chat(system_prompt = system_prompt, user_input = user_prompt, enable_search=True)
        self.memory_manager.add_conversation(message, response)
        return response

    def update_state(self, new_state: str):
        """更新Agent状态"""
        old_state = self.current_state
        self.current_state = new_state
        print(f"Agent状态更新: {old_state} -> {new_state}")
        


    def stop(self):
        """停止Agent,停止所有线程"""
        logger.info("开始关闭服务...")
        try:
            loop = asyncio.get_running_loop()  # 获取当前事件循环
            tasks = asyncio.all_tasks(loop)  # 获取所有正在运行的任务
            for task in tasks:  # 取消所有任务
                task.cancel()
            sys.exit(0)
        except RuntimeError as e:
            if "no running event loop" in str(e):
                logger.info("事件循环已关闭，无需额外操作")
            else:
                logger.error(f"停止服务时发生异常: {str(e)}")
        logger.info("所有服务已停止")






