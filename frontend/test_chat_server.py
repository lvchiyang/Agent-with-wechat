import json
import websockets

def test_message_validation():
    # 有效私聊消息
    valid_private = {
        "id": "1694773800",
        "category": "私聊",
        "friend_name": "用户A",
        "text": "你好！",
        "group_name": "",
        "image": ""
    }
    
    # 有效群聊消息
    valid_group = {
        "id": "1694773850",
        "category": "群聊",
        "friend_name": "用户B",
        "group_name": "测试群组",
        "text": "大家好！",
        "image": ""
    }
    
    # 无效消息（缺少friend_name）
    invalid_msg = {
        "id": "1694773900",
        "category": "私聊",
        "text": "测试消息"
    }
    
    handler = WebSocketHandler()
    assert handler._parse_message(json.dumps(valid_private)) is not None
    assert handler._parse_message(json.dumps(valid_group)) is not None
    assert handler._parse_message(json.dumps(invalid_msg)) is None 

async def test_websocket_connection():
    async with websockets.connect("ws://localhost:9001/chat") as websocket:
        # 测试有效消息
        valid_msg = {
            "id": "123",
            "category": "私聊",
            "friend_name": "测试用户",
            "text": "测试消息"
        }
        await websocket.send(json.dumps(valid_msg))
        response = await websocket.recv()
        assert "测试消息" in response
        
        # 测试无效消息
        invalid_msg = {"text": "无效消息"}
        await websocket.send(json.dumps(invalid_msg))
        response = await websocket.recv()
        assert "错误" in response 