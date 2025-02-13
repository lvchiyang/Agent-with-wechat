import React, { useState } from 'react';

const ChatInterface = () => {
    const [message, setMessage] = useState('');
    const [friendName, setFriendName] = useState('ycy');
    const [groupName, setGroupName] = useState('');
    const [chatHistory, setChatHistory] = useState([]);

    const sendMessage = async () => {
        const payload = {
            id: Date.now(), // 添加时间戳
            category: groupName ? '群聊' : '私聊', // 根据群聊名称判断类型
            friend_name: friendName,
            group_name: groupName || null, // 使用null代替undefined
            text: message,
            image: null // 添加图片字段
        };

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            // 更新聊天记录...
        } catch (error) {
            console.error('发送失败:', error);
        }
    };

    return (
        <div className="chat-container">
            <div className="config-panel">
                <input
                    type="text"
                    placeholder="朋友名称"
                    value={friendName}
                    onChange={(e) => setFriendName(e.target.value)}
                />
                <input
                    type="text"
                    placeholder="群聊名称（可选）"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                />
            </div>
            
            <div className="chat-history">
                {chatHistory.map((msg, index) => (
                    <div key={index} className="message">
                        <span className="sender">{msg.sender}:</span>
                        <p>{msg.content}</p>
                    </div>
                ))}
            </div>
            
            <div className="input-area">
                <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="输入消息..."
                />
                <button onClick={sendMessage}>发送</button>
            </div>
        </div>
    );
};

export default ChatInterface; 