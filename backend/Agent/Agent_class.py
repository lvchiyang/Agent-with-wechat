import logging
from backend.channel.chat_server import ChatServer
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
        self.LLM_Client = LLM_Client()
        self.memory_manager = MemoryManager(self.LLM_Client)
        self.prompt_manager = PromptManager()
        self.chat_server = ChatServer(self.handle_message)
        self.current_state = "idle"  # 添加当前状态
        # 传递memory实例给Plan
        self.plan = Plan(self.update_state, self.memory_manager, self.LLM_Client)


    def start(self):
        try:
            logger.info("Starting Agent")
            # 创建事件循环并运行异步任务
            async def main_loop():
                await asyncio.gather(
                    asyncio.to_thread(self.plan.start),
                    asyncio.to_thread(self.chat_server.run)
                )
            asyncio.run(main_loop())
            logger.info("Agent started successfully")
        except Exception as e:
            logger.error(f"Error starting Agent: {str(e)}")
            self.stop()

    def stop(self):
        """停止Agent,停止所有线程"""
        logger.info("开始关闭服务...")
        self.chat_server.stop()
        self.plan.stop()
        # 添加资源清理逻辑
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        logger.info("所有服务已停止")

    async def handle_message(self, message: dict) -> str:  
        # 提供上下文
        context = self.memory_manager.new_message(message) 
        related_memories = self.memory_manager.query_context(message)
        prompt_manager = self.prompt_manager.get_system_prompt(related_memories, context, self.current_state)        
        response = await self.LLM_Client.chat(system_prompt = prompt_manager, user_input = message["text"], enable_search=True)

        if response == "对话已经完成":
            response = None

        self.memory_manager.add_conversation(message, response)

        return response

    def update_state(self, new_state: str):
        """更新Agent状态"""
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"Agent状态更新: {old_state} -> {new_state}")
        # 这里可以添加状态变化时的其他处理逻辑










