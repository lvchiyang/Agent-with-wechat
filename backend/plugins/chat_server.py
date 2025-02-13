from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from fastapi import WebSocket
from backend.LLM.LLM_Client import LLM_Client
from backend.LLM.prompt_manager import PromptManager
from backend.plugins.rate_limiter import RateLimiter
import logging

logger = logging.getLogger(__name__)
'''
聊天服务器
搭起来了，Agent实现对话，同时还可以做别的事情。现在先验证一下这一步。

下一步；
聊天服务器直接llm对接，和Agent没有多大关系，那不行，需要是以Agent为核心，
需要是当Agent收到消息，Agent对信息进行处理，由Agent决定是否需要调用llm，还是调用其他服务，然后由Agent决定把消息发送给谁。

'''


class WebSocketHandler:
    def __init__(self, message_callback=True):
        self.message_callback = message_callback
        # self.LLM_Client = LLM_Client()
        self.prompt_manager = PromptManager()
        self.websocket = None
        self.should_continue = True  # 添加控制循环的变量

    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        self.websocket = websocket
        
        try:
            while self.should_continue:  # 使用变量控制循环
                # 接收用户消息
                message = await websocket.receive_text()
                
                if self.message_callback:
                    print(f"收到消息: {message}")
                    
                    # response = await self.message_callback(message)
                    # await websocket.send_text(response) # 等Agent处理完
                else:
                    await websocket.send_text("No message handler configured")
                    
        except Exception as e:
            print(f"Error: {e}")
            await websocket.send_text(f"系统错误: {str(e)}")
        finally:
            await websocket.close()

    def stop_connections(self):
        """停止所有连接的循环"""
        self.should_continue = False

class ChatServer:
    def __init__(self):
        self.app = FastAPI()
        self.rate_limiter = RateLimiter(
            max_requests=100,  # 每分钟最多100次请求
            interval=60,
            ban_duration=300
        )
        self.websocket_handler = WebSocketHandler()
        self._setup()
        self.server = None  # 添加server实例引用
        self.should_stop = False  # 添加停止标志

    def _setup(self):
        # 允许跨域
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 注册WebSocket路由
        @self.app.websocket("/chat")
        async def websocket_endpoint(websocket: WebSocket):
            # 如果服务正在停止，拒绝新连接
            if self.should_stop:
                await websocket.close(code=1008, reason="Server is shutting down")
                return
                
            # 速率限制检查
            if self.rate_limiter.is_rate_limited(websocket):
                await websocket.close(code=1008, reason="Rate limit exceeded")
                return
                
            await self.websocket_handler.handle_connection(websocket)

    def start(self):
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=9001,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(
            target=self.server.run,
            daemon=True
        )
        self.thread.start()

    def stop(self):
        """优雅停止服务器"""
        try:
            self.should_stop = True
            self.websocket_handler.stop_connections()  # 停止所有连接的循环
            if self.server:
                self.server.should_exit = True
                self.server.force_exit = True
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5)
                    if self.thread.is_alive():
                        logger.warning("Server did not stop gracefully, forcing exit")
            logger.info("Chat server stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping chat server: {str(e)}")

    def stop_connections(self):
        """停止所有连接的循环"""
        self.websocket_handler.stop_connections() 