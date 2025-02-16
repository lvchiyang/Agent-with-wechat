import yaml
from pathlib import Path
from client import GewechatClient

class GeweChannel:
    def __init__(self):
        # 配置文件路径
        self.CONFIG_PATH = Path(__file__).parent / "config/config.yaml"
        self.group_dict_PATH = Path(__file__).parent / "config/group_dict.yaml"
        
        # 加载配置
        self.config = self.load_config()
        self.group_dict = self.load_group_dict()
        
        # 初始化配置
        self.trigger_prefix = self.config['filter'].get('trigger_prefix', "")
        self.app_id = self.config['gewechat'].get('app_id', "")
        self.token = self.config['gewechat'].get('token', "")
        self.base_url = self.config['gewechat'].get('base_url', "")
        self.callback_url = self.config['gewechat'].get('callback_url', "")
        self.client = GewechatClient(self.base_url, self.token)
        
        # 检查登录状态
        self.check_login_status()

        # 每次登录，获取通信录群聊字典
        contacts_list = self.client.fetch_contacts_list(self.app_id).get('data', {}).get('chatrooms', [])
        self.group_dict = {item: None for item in contacts_list}
        self.save_group_dict()  # 使用新的保存方法

    def connect(self):
        # 初始化客户端
        self.client = GewechatClient(self.base_url, self.token)

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

    def check_login_status(self):
        """检查登录状态，未登录则执行登录流程"""

        self.app_id = self.client.login(self.app_id)[0]
        self.token = self.client.get_token().get('data', "")
            
        # 保存新配置
        self.config['gewechat'].update({
            'app_id': self.app_id,
            'token': self.token
        })
        self.save_config()
        print("登录信息已保存至配置文件")

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
            # TypeName = message_dict.get("TypeName", "") # 这个好像没什么用，因为不知道TypeName的含义
            data = message_dict.get("Data", {})
            Wxid = group_id = data.get("FromUserName", {}).get("string", "")
            PushContent = data.get("PushContent", "")
            category = "私聊"
            group_name = ""
            friend_name = ""
            
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
            
            if text.startswith(self.trigger_prefix):
                return {
                    "id": Wxid,
                    "category": category,
                    "friend_name": friend_name if friend_name else "",
                    "group_name": group_name if group_name else "",
                    "text": text if text else "",
                }

        except Exception as e:
            print(f"消息解析失败: {e}")
            return {}
        

    def post_text(self, answer: dict):
        """发送回复的统一入口"""
        self.client.post_text(self.app_id, answer["id"],answer["response"])

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

