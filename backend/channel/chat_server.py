import asyncio
import threading
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from queue import Queue
from typing import Dict, Any
import uvicorn
from .gewechat.gewe_channel import GeweChannel
import re
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import time

logger = logging.getLogger(__name__)

class ChatServer():
    def __init__(self, message_callback, new_message):
        self.message_callback = message_callback
        self.channel = GeweChannel()
        self.message_queue = asyncio.Queue()
        self.app = FastAPI()
        parsed = urlparse(self.channel.callback_url) # 解析URL参数
        self.server_port = parsed.port or 9001  
        self.api_path = parsed.path.rstrip('/') or '/v2/api/callback/collect'  # 默认路径
        self.server = None  
        # self.new_message = asyncio.Event()  
        self.running = True
        self.new_message = new_message
        self._setup_routes()

    def _setup_routes(self):
        # 添加路由定义
        @self.app.post("/v2/api/callback/collect")
        async def handle_callback(request: Request):  # 移除了self参数
            try:
                data = await request.json()
                # print(f"收到消息: {data}")
                
                # 测试消息处理
                if data.get("testMsg"):
                    if data["testMsg"] == "回调地址链接成功！":
                        return self._format_response(200, "连接成功", {
                            "server_info": f"running on port {self.server_port}"
                        })
                    return self._format_response(400, "无效的测试消息")
                
                await self.message_queue.put(data)
                self.new_message.set()
                # print("消息已接收")

                # 立即返回接收成功响应
                return self._format_response(200, "消息已接收", {"status": "processing"})
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                return self._format_response(400, "无效的JSON格式")
            except Exception as e:
                logger.critical(f"未处理的全局异常: {str(e)}", exc_info=True)
                return self._format_response(500, "服务器内部错误", {"exception": str(e)})

    def run_server(self):
        self.new_message.set()
        uvicorn.run(self.app, host="0.0.0.0", port=9001)


    async def message_processor(self):
        """消息处理协程"""
        while self.running:
            await self.new_message.wait()
            while not self.message_queue.empty():
                message = await self.message_queue.get()
                try:
                    parsed_msg = self.channel.parse_message(message)
                    print(f"正在处理消息: {parsed_msg}")
                    if parsed_msg:
                        try:
                            response = await self.message_callback(parsed_msg)
                            self.channel.post_text(parsed_msg['id'], response)
                        except Exception as e:
                            logger.error(f"消息处理链异常: {str(e)}", exc_info=True)
                except Exception as e:
                    print(f"Error processing message: {str(e)}")

    async def init_gewechat_channel(self):
        try:
            print("开始初始化微信通道...")
            self.channel.login()
            await asyncio.sleep(1)
            await self.channel.connect()
        except Exception as e:
            logger.error(f"微信通道初始化失败: {str(e)}")

    def _format_response(self, ret: int, msg: str, data=None):
        return JSONResponse({
            "ret": ret,
            "msg": msg,
            "data": data or {},
            "server_port": self.server_port,
            "api_path": self.api_path
        })