from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import traceback
import threading
from gewe_channel import GeweChannel

config_path = "config/config.yaml"

'''
要求的message数据格式是:
{
    "id": str,  # wxid
    "category": 私聊/群聊
    "friend_name": friend_name # 朋友/user姓名
    "group_name": group_name # 群聊名称，可为空
    "text": text  # 对话内容
    # "image": image,  # 图片信息，为空，NULL或者None，而不是null
} 
'''

app = FastAPI()
channel = None  # 全局通道实例

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=9001)

@app.post("/v2/api/callback/collect")
async def collect(request: Request):
    try:
        data = await request.json()
        print(f"收到消息: {data}")
        process_message(data)
        
    except Exception as e:
        print(f"消息处理失败: {str(e)}")

def process_message(data: dict):
    try:
        global channel
        if not channel:
            raise RuntimeError("Channel 未初始化！")
            
        message = channel.parse_message(data)
        if message:
            answer = {"id": "wxid_xyswpdll2tsh22", "response": "处理完成"}
            channel.post_text(answer) 
        else:
            print("是要被忽略的消息")  
            
    except Exception as e:
        print(f"消息处理失败: {str(e)}")
        traceback.print_exc()

def initialize_channel():
    global channel
    try:
        channel = GeweChannel()
        print("通道初始化成功")
        channel.connect()
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        traceback.print_exc()
        # 重要：初始化失败时退出程序
        import sys
        sys.exit(1)

if __name__ == "__main__":
    # 先启动服务器线程
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 等待服务器启动后初始化通道
    import time
    time.sleep(1)  # 给服务器启动留出时间
    initialize_channel()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n服务器关闭")