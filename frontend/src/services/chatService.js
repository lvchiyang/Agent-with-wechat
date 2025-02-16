class ChatService {
    constructor() {
        this.ws = new WebSocket('ws://localhost:9001/chat');
        // 添加心跳检测
        this.keepAlive = setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({type: 'ping'}));
            }
        }, 30000);
    }

    sendMessage(message) {
        const msg = {
            id: Date.now().toString(),
            category: message.isGroup ? "群聊" : "私聊",
            friend_name: message.friendName,
            group_name: message.groupName || "",
            text: message.text,
            image: ""
        };
        // 添加发送状态检查
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(msg));
        } else {
            console.error('WebSocket连接未就绪');
        }
    }
} 