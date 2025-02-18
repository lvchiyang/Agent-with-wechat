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

class ChatServer(threading.Thread):
    def __init__(self, message_callback):
        super().__init__(daemon=True)
        self.channel = GeweChannel()
        
        # 解析URL参数
        parsed = urlparse(self.channel.callback_url)
        self.server_port = parsed.port or 80  # 默认端口80
        self.api_path = parsed.path  # 获取路径如 /v2/api/callback/collect

        # 验证路径格式
        if not re.match(r"^/[\w/-]+$", self.api_path):
            raise ValueError(f"Invalid API path: {self.api_path}")

        self.message_queue = asyncio.Queue()
        self.app = FastAPI()
        self._setup_routes()
        self.message_callback = message_callback
        self.running = False
        self.server_started_event = asyncio.Event()  # 新增启动完成事件

    def _setup_routes(self):
        # 动态配置路由路径
        @self.app.post(self.api_path)
        async def receive_message(request: Request):
            data = await request.json()
            await self.message_queue.put(data)
            return JSONResponse({"status": "received"})

    async def _message_processor(self):
        """消息处理协程"""
        while self.running:
            if not self.message_queue.empty():
                message = await self.message_queue.get()
                await self._process_message(message)
            await asyncio.sleep(1)  # 防止CPU占用过高

    async def _process_message(self, message: Dict[str, Any]):
        """实际处理消息的逻辑"""
        try:
            parsed_msg = self.channel.parse_message(message)
            if parsed_msg:
                response = await self.message_callback(parsed_msg)
                response = {"id": parsed_msg['id'], "text": str(response)}
                self.channel.post_text(response)
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")

    async def _run_server(self):
        """启动FastAPI服务器"""
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.server_port,  # 使用解析的端口
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        self.server_started_event.set()  # 服务器启动后触发事件

    async def _main_loop(self):
        """主事件循环"""
        self.running = True
        server_task = asyncio.create_task(self._run_server())
        processor_task = asyncio.create_task(self._message_processor())
        
        # 等待服务器启动完成
        await self.server_started_event.wait()
        
        # 服务器启动后立即连接
        self.channel.connect()
        
        processor_task = asyncio.create_task(self._message_processor())
        await asyncio.gather(server_task, processor_task)

    def run(self):
        """线程入口点"""
        asyncio.run(self._main_loop())
        print("ChatServer run")

    def stop(self):
        """停止服务器"""
        self.running = False