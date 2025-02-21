import yaml
import json
import asyncio
from pathlib import Path
from .client import GewechatClient
from .util.terminal_printer import print_yellow, make_and_print_qr, print_green

class GeweChannel:
    def __init__(self):
        # 配置文件路径
        self.CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "gewe_config.yaml"
        self.group_dict_PATH = Path(__file__).parent.parent.parent / "config" / "group_dict.yaml"
        
        # 加载配置
        self.config = self.load_config()
        self.group_dict = self.load_group_dict()
        
        # 初始化配置
        self.trigger_prefix = self.config['filter'].get('trigger_prefix', "")
        self.app_id = self.config['gewechat'].get('app_id', "")
        self.base_url = self.config['gewechat'].get('base_url', "")
        self.callback_url = self.config['gewechat'].get('callback_url', "")
        self.wxid = self.config['gewechat'].get('wxid', "")

        # 获取token
        self.token = GewechatClient.get_token(self.base_url).get('data', "")
        # print(f"token: {self.token}")

        # 初始化客户端
        self.client = GewechatClient(self.base_url, self.token)
    
    def login(self):
        # 尝试三次
        for attempt in range(1, 4):  # 从1到3，尝试3次
            try:
                print(f"尝试登录，第 {attempt} 次...")
                self.wechat_login()  # 调用微信登录方法
                break  # 登录成功后退出循环
            except Exception as e:
                print(f"登录失败，第 {attempt} 次: {e}")
                self.client.log_out(self.app_id)
                if attempt == 3:  # 如果是第3次尝试失败
                    print("已达到最大尝试次数，登录失败。")
                    raise RuntimeError("登录失败，已达到最大尝试次数。")  # 抛出自定义异常


    async def connect(self, max_retries=3):
        for attempt in range(max_retries):
            print(f"尝试连接，第 {attempt+1} 次...")
            try:
                self.client.set_callback(self.token, self.callback_url)
                print_green("连接成功")
                break
            except Exception as e:
                print(f"连接失败，第 {attempt+1} 次: {e}")
                if attempt == max_retries-1:
                    await asyncio.sleep(5 * (attempt+1))  # 指数退避
                    raise

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except FileNotFoundError:
            print(f"Config file not found at {self.CONFIG_PATH}")  # 添加调试信息
    
    def save_config(self):
        """保存配置文件"""
        with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.config, f, allow_unicode=True)

    def load_group_dict(self):
        """加载群组列表"""
        try:
            with open(self.group_dict_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {'group_dict': []}
                return config['group_dict']
        except FileNotFoundError:
            print(f"Group list file not found at {self.group_dict_PATH}")
            return []

    def save_group_dict(self):
        """保存群组列表"""
        with open(self.group_dict_PATH, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'group_dict': self.group_dict}, f, allow_unicode=True)


    def wechat_login(self):
        """检查登录状态，未登录则执行登录流程"""
        try:
            self.app_id,_= self.client.login(self.app_id)
            # print(f"登录成功，app_id: {self.app_id}")

            # 保存新配置
            self.config['gewechat'].update({
                'app_id': self.app_id
            })
            self.save_config()
            print("登录信息已保存至配置文件")
            self._get_contacts_roomchat()
        except Exception as e:
            print(f"登录失败: {e}")
            raise RuntimeError(json.dumps(e))

    def _get_contacts_roomchat(self):
        try:
            """获取wwid"""
            self.wxid = self.client.get_profile(self.app_id).get('data', {}).get('wxid', "")
            self.config['gewechat'].update({
                'wxid': self.wxid
            })
            self.save_config()
            # print_green(f"成功获取wwid: {self.wxid}")

            """获取通信录群聊字典"""
            contacts_list = self.client.fetch_contacts_list(self.app_id).get('data', {}).get('chatrooms', [])
            self.group_dict = {item: None for item in contacts_list}
            self.save_group_dict()  # 使用新的保存方法
            # print_green(f"成功获取通信录群聊")
        except Exception as e:
            print(f"获取通信录群聊失败: {e}")
            raise RuntimeError(json.dumps(e))

    def get_client(self):
        """获取GewechatClient实例"""
        return self.client

    def get_config(self):
        """获取当前配置"""
        return {
            'app_id': self.app_id,
            'token': self.token,
            'base_url': self.base_url,
            'callback_url': self.callback_url
        }



    # 得先看功能需要什么信息
    '''
    Wxid
    category
    friend_name
    group_name
    text
    ''' # 目前只处理文本聊天消息
    def parse_message(self, message_dict: dict) -> dict:
        """解析原始消息"""
        try:
            if message_dict.get("testMsg") == "回调地址链接成功！":
                return None
            # TypeName = message_dict.get("TypeName", "") # 这个好像没什么用，因为不知道TypeName的含义
            TypeName = message_dict.get("TypeName", "")
            data = message_dict.get("Data", {})
            MsgType = data.get("MsgType", "")

            group_id = data.get("FromUserName", {}).get("string", "")
            Wxid = group_id
            PushContent = data.get("PushContent", "")
            category = "私聊"
            group_name = ""
            friend_name = ""
            text = ""

            if Wxid == self.wxid:  # 过滤掉来自自己的消息
                return None
            
            if MsgType != 1: # 目前仅支持文本消息
                print(f"消息: {message_dict}")
                return None
            
            if TypeName == "AddMsg":
                # 判断是否是群消息
                if '@' in group_id:
                    # 判断是否是通讯录群消息
                    if group_id in self.group_dict:
                        group_name = self.group_dict.get(group_id, "")
                        category = "群聊"
                        if not group_name:
                            group_name = self.client.get_chatroom_info(self.app_id, group_id).get('data', {}).get('nickName', "")
                            self.group_dict[group_id] = group_name
                            self.save_group_dict()  # 使用新的保存方法
                    
                    else: # 非通讯录群消息，丢弃
                        return None
                
                # 解析PushContent
                if ": " in PushContent:
                    friend_name, text = PushContent.split(": ", 1)
                
                msg = {
                        "id": Wxid,
                        "category": category,
                        "friend_name": friend_name if friend_name else "",
                        "group_name": group_name if group_name else "",
                        "text": text if text else "",
                    }
                if category == "私聊":
                    return msg
                elif text.startswith(self.trigger_prefix):
                    return msg
                else:
                    return None   
            else:
                print(f"消息: {message_dict}")
                return None

        except Exception as e:
            print(f"消息解析失败: {e}")
            return None
        

    def post_text(self, id, response):
        """发送回复的统一入口"""
        self.client.post_text(self.app_id, id, response)

    # def _handle_message(self, msg: dict):
    #     """处理单条消息"""
    #     # 根据消息类型调用不同的API
    #     if msg.get('type') == 'text':
    #         self._handle_text_message(msg)
    #     elif msg.get('type') == 'image':
    #         self._handle_image_message(msg)
    #     # 其他消息类型...

    # def _handle_image_message(self, msg: dict):
    #     """处理图片消息"""
    #     # 调用client.py的API下载图片
    #     self.client.download_image(
    #         app_id=self.app_id,
    #         xml=msg['xml'],
    #         type=msg['type']
    #     )

if __name__ == "__main__":
    channel = GeweChannel()
    print(f"当前使用的app_id: {channel.app_id}")
    print(f"当前使用的token: {channel.token}")

