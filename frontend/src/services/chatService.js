class ChatService {
    constructor() {
        this.ws = new WebSocket('ws://localhost:9001/chat');
    }

    sendMessage(message) {
        const msg = {
            id: Date.now().toString(),
            category: message.isGroup ? "群聊" : "私聊",
            friend_name: message.friendName,
            group_name: message.groupName || "",
            text: message.text,
            image: "" // 保持空值
        };
        this.ws.send(JSON.stringify(msg));
    }
} 