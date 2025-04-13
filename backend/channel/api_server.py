from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class APIServer:
    def __init__(self, handle_message, new_message_event):
        self.app = FastAPI()
        self.handle_message = handle_message
        self.new_message_event = new_message_event
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 在生产环境中应该设置具体的域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    message = await websocket.receive_text()
                    message_data = json.loads(message)
                    
                    # 处理消息
                    response = await self.handle_message(message_data)
                    
                    # 发送响应
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "content": response
                    }))
                    
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await websocket.close()
    
    def run_server(self, host="0.0.0.0", port=8000):
        import uvicorn
        uvicorn.run(self.app, host=host, port=port) 