import json
import yaml
from client import GewechatClient
from pathlib import Path

class config:
    def __init__(self):
        # 配置文件路径
        self.CONFIG_PATH = Path(__file__).parent / "config/config.yaml"
        self.group_dict_PATH = Path(__file__).parent / "config/group_dict.yaml"
        
        # 加载配置
        self.config = self.load_config()
        self.group_dict = self.load_group_dict()
        
        # 初始化配置
        self.app_id = self.config['gewechat'].get('app_id', "")
        self.token = self.config['gewechat'].get('token', "")
        self.base_url = self.config['gewechat'].get('base_url', "")
        self.callback_url = self.config['gewechat'].get('callback_url', "")

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {'gewechat': {}}
                return config
        except FileNotFoundError:
            print(f"Config file not found at {self.CONFIG_PATH}")  # 添加调试信息
            return {'gewechat': {}}
    
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

if __name__ == "__main__":
    # app_id = "wx_LdauLALCj7rrWlHhdwAZm"
    # token = "881f5e8b13a84509a284c17e429d9ee1" 
    # base_url = "http://192.168.31.189:2531/v2/api"
    # callback_url = "http://192.168.31.176:9001/v2/api/callback/collect"
    # download_url = "http://192.168.31.189:2532/download"

    cfg = config()
    # print(cfg.app_id)
    group_id = "24862693104@chatroom"

    client = GewechatClient(cfg.base_url, cfg.token)

    # contacts_list = client.fetch_contacts_list(cfg.app_id).get('data', {}).get('chatrooms', [])
    # cfg.group_dict = {item: None for item in contacts_list}
    # cfg.save_group_dict()  # 使用新的保存方法

    # if group_id in cfg.group_dict:
    #     group_name = cfg.group_dict.get(group_id, "")
    #     category = "群聊"
    #     if not group_name:
    #         group_name = client.get_chatroom_info(cfg.app_id, group_id).get('data', {}).get('nickName', "")
    #         cfg.group_dict[group_id] = group_name
    #         cfg.save_group_dict()  # 使用新的保存方法
    # contacts_list = client.get_chatroom_info(cfg.app_id, "24862693104@chatroom").get('data', {}).get('nickName', "")
    # print(contacts_list.get('data', {}).get('chatrooms', []))
    # group_name = client.get_chatroom_info(cfg.app_id, "24862693104@chatroom").get('data', {}).get('nickName', "")
    # cfg.group_dict.append({"248626troom": group_name})
    # cfg.save_group_dict()  # 使用新的保存方法
    
    answer = {"id": "wxid_xyswpdll2tsh22", "response": "处理完成"}

    wxid = "wxid_xyswpdll2tsh22"
    post_text = client.post_text(cfg.app_id, answer["id"], answer["response"])
    print(post_text)