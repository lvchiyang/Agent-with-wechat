from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from fastapi import WebSocket
from backend.LLM.prompt_manager import PromptManager
from backend.channel.rate_limiter import RateLimiter
from backend.plugins.get_time import get_current_time
import logging
import json
from typing import Optional
from fastapi import WebSocketDisconnect
import asyncio
import time     
from fastapi import FastAPI, Request, BackgroundTasks

from backend.channel.gewechat.chat_server_test import GeweChannel

logger = logging.getLogger(__name__)
channel = None  # 全局通道实例

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
        self.processing_task = None  # 添加后台处理任务引用

    def _setup(self):
        # 允许跨域
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 改为HTTP POST接口
        @self.app.post("/v2/api/callback/collect")
        async def receive_message(request: Request, background_tasks: BackgroundTasks):
            try:
                data = await request.json()
                # message = self._parse_message(data)  # 直接解析请求体
                
                # if not message:
                #     return {"status": "error", "message": "无效的消息格式"}
                
                await self._process_messages(data)
                # 将消息放入队列并立即返回响应
                # await self.message_queue.put(data)
                # background_tasks.add_task(self._start_processing)  # 添加后台处理任务
                
                # return {"status": "success", "message": "消息已接收"}
                
            except json.JSONDecodeError:
                print (f"status: error, message: 无效的JSON格式")
            except Exception as e:
                logger.error(f"请求处理错误: {str(e)}")
                print (f"status: error, message: 服务器内部错误")



    async def _process_messages(self, message):
        """持续处理消息队列中的消息"""
        # global channel
        # message = await self.message_queue.get()
        try:
            if self.message_callback:
                async with self.lock:
                    print(f"message:{message}")

                    parsed_msg = channel.parse_message(message)
                    print(f"parsed_msg:{parsed_msg}")

                    if parsed_msg:
                        response = await self.message_callback(parsed_msg)
                        response = {"id": parsed_msg['id'], "text": "response"}
                        channel.post_text(response)
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")
        # finally:
            # self.message_queue.task_done()

    # def _parse_message(self, data: dict) -> Optional[dict]:
    #     """直接验证请求体字典"""
    #     try:
    #         # 验证必要字段
    #         required_fields = ['id', 'category', 'friend_name', 'text']
    #         if not all(key in data for key in required_fields):
    #             raise ValueError("缺少必要字段")
            
    #         # 验证category值
    #         if data['category'] not in ['私聊', '群聊']:
    #             raise ValueError("无效的对话类型")
            
    #         # 群聊必须包含group_name
    #         if data['category'] == '群聊' and not data.get('group_name'):
    #             raise ValueError("群聊必须提供group_name")
            
    #         # 清理文本内容
    #         data['text'] = data['text'].strip()[:500]
    #         data.setdefault('image', None)
            
    #         return data
            
    #     except ValueError as e:
    #         logger.warning(f"无效消息格式: {str(e)}")
    #         return None


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

        global channel
        time.sleep(1)  # 给服务器启动留出时间
        channel = GeweChannel()
        if not channel:
            raise RuntimeError("Channel 未初始化！")
        channel.connect()

    # async def _start_processing(self):
    #     """启动消息处理（如果尚未运行）"""
    #     if not self.processing and not self.processing_task:
    #         self.processing = True
    #         self.processing_task = asyncio.create_task(self._process_messages())

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

