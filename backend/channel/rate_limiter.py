import time
from collections import defaultdict
from typing import Optional
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(
        self,
        max_requests: int = 100,
        interval: int = 60,  # 秒
        ban_duration: int = 300  # 秒
    ):
        self.max_requests = max_requests
        self.interval = interval
        self.ban_duration = ban_duration
        self.request_records = defaultdict(list)
        self.banned_clients = {}

    def _get_client_id(self, websocket: WebSocket) -> Optional[str]:
        """获取客户端唯一标识"""
        try:
            return websocket.client.host  # 使用IP地址作为标识
        except AttributeError:
            return None

    def is_rate_limited(self, websocket: WebSocket) -> bool:
        """检查是否超过速率限制"""
        client_id = self._get_client_id(websocket)
        if not client_id:
            return False

        # 检查是否在封禁名单
        if client_id in self.banned_clients:
            if time.time() < self.banned_clients[client_id]:
                return True
            del self.banned_clients[client_id]

        # 清理过期记录
        now = time.time()
        self.request_records[client_id] = [
            t for t in self.request_records[client_id]
            if t > now - self.interval
        ]

        # 添加新记录
        self.request_records[client_id].append(now)

        # 检查是否超过限制
        if len(self.request_records[client_id]) > self.max_requests:
            self.banned_clients[client_id] = now + self.ban_duration
            logger.warning(f"Rate limit exceeded for {client_id}")
            return True

        return False 