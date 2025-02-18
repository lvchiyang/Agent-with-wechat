from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from fastapi import WebSocket
from backend.LLM.prompt_manager import PromptManager
from backend.plugins.rate_limiter import RateLimiter
from backend.plugins.get_time import get_current_time
import logging
import json
from typing import Optional
from fastapi import WebSocketDisconnect
import asyncio
import time

logger = logging.getLogger(__name__)
'''
聊天服务器
搭起来了，Agent实现对话，同时还可以做别的事情。现在先验证一下这一步。

下一步；
聊天服务器直接llm对接，和Agent没有多大关系，那不行，需要是以Agent为核心，
需要是当Agent收到消息，Agent对信息进行处理，由Agent决定是否需要调用llm，还是调用其他服务，然后由Agent决定把消息发送给谁。

'''



class ChatServer:
    def __init__(self, message_callback):
        self.app = FastAPI()
        self.rate_limiter = RateLimiter(
            max_requests=100,  # 每分钟最多100次请求
            interval=60,
            ban_duration=300
        )
        self._setup()
        self.server = None  # 添加server实例引用
        self.should_stop = False  # 添加停止标志
        self.message_callback = message_callback
        self.prompt_manager = PromptManager()
        self.websocket = None
        self.lock = asyncio.Lock()
        self.message_queue = asyncio.Queue()
        self.processing = False

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
            try:
                await websocket.accept()
                # 启动消息处理任务
                processing_task = asyncio.create_task(self._process_messages(websocket))
                
                while True:
                    # 接收消息
                    message_str = await websocket.receive_text()
                    message = self._parse_message(message_str)
                    
                    if not message:
                        await websocket.send_text(json.dumps({
                            "type": "system",
                            "status": "error",
                            "message": "无效的消息格式"
                        }))
                        continue
                    
                    # 将消息放入队列
                    await self.message_queue.put(message)
                    
            except WebSocketDisconnect:
                logger.info("客户端断开连接")
                processing_task.cancel()  # 取消处理任务
            except Exception as e:
                logger.error(f"WebSocket错误: {str(e)}")
                processing_task.cancel()  # 取消处理任务
                await websocket.close(code=1011, reason=str(e))
                
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


    async def _process_messages(self, websocket):
        """处理消息队列中的消息"""
        while True:
            message = await self.message_queue.get()
            try:
                if self.message_callback:
                    async with self.lock:  # 使用异步锁
                        response = await self.message_callback(message)
                    # 修改响应格式为前端需要的JSON结构
                    await websocket.send_text(json.dumps({
                        "type": "message",
                        "text": response,
                        "timestamp": int(time.time() * 1000)
                    }))
            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}")
            finally:
                self.message_queue.task_done()

    def _parse_message(self, message_str: str) -> Optional[dict]:
        """解析和验证消息格式"""
        try:
            message = json.loads(message_str)
            
            # 验证必要字段
            required_fields = ['id', 'category', 'friend_name', 'text']
            if not all(key in message for key in required_fields):
                raise ValueError("缺少必要字段")
            
            # 验证category值
            if message['category'] not in ['私聊', '群聊']:
                raise ValueError("无效的对话类型")
            
            # 群聊必须包含group_name
            if message['category'] == '群聊' and not message.get('group_name'):
                raise ValueError("群聊必须提供group_name")
            
            # 清理文本内容
            message['text'] = message['text'].strip()[:500]
            message.setdefault('image', None)
            
            return message
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"无效消息格式: {message_str}，错误: {str(e)}")
            return None


    async def stop_connections(self):
        """关闭所有WebSocket连接"""
        try:
            if self.websocket:
                await self.websocket.close(code=1000, reason="Server shutting down")
        except Exception as e:
            logger.error(f"关闭WebSocket连接时出错: {str(e)}")

    def stop(self):
        """优雅停止服务器"""
        try:
            self.should_stop = True
            
            # 停止所有连接的循环
            asyncio.run(self.stop_connections())
            
            # 停止服务器
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

