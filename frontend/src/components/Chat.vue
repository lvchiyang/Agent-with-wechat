export default {
    methods: {
        handleMessage(event) {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'system') {
                    this.handleSystemMessage(message);
                } else if (message.type === 'message') {
                    this.displayMessage(message);
                }
            } catch (e) {
                console.error('消息解析失败', e);
            }
        },
        handleSystemMessage(msg) {
            if (msg.status === 'error') {
                this.showError(msg.message);
            }
        }
    }
} 