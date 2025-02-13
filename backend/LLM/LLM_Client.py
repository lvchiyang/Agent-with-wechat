from backend.LLM.AliyunLLM import AliyunLLM
from backend.LLM.prompt_manager import PromptManager
import yaml
from pathlib import Path
from typing import List, Dict
import json
from backend.LLM.aliyun_embedding import AliyunMultimodalEmbedding

'''
这个文件是用来处理大模型的，包括初始化大模型、获取embedding、调用大模型进行对话
我希望在这个代码当中进行一个封装：
1. 配置要使用的模型
2. 准备好所有模型通用的API，而不是进到一个个云服务商的API调用代码里面去找。

这篇代码，作为所有LLM API的抽象层。


AliyunMultimodalEmbedding支持的message最长只能占512个token，太多就会被截断
图片JPG、PNG、BMP，支持以Base64格式或URL形式输入。接受的图片大小上限为 3MB
每分钟调用限制（RPM）：120
需要处理成：
{
    "contents": [ 
        {"text": "通用多模态表征模型"},
        {"image": "https://xxxx.com/xxx/images/xxx.jpg"},
        {"vedio": "https://xxx.com/xxx/video/xxx.mp4"}
    ]
}
'''

class LLM_Client:
    def __init__(self):
        self.llm = None
        self.prompt_manager = PromptManager()
        self._load_config()
        self.embedding = AliyunMultimodalEmbedding()

    def _load_config(self):
        # 获取项目根目录
        BASE_DIR = Path(__file__).resolve().parent.parent

        # 加载配置
        config_path = BASE_DIR / "config" / "settings.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 初始化大模型
        self.llm = AliyunLLM(
            api_key=config["llm"]["params"]["ali_qwen"]["api_key"],
            model_version=config["llm"]["params"]["ali_qwen"]["version"]
        )

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        调用大模型进行对话
        
        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "你好"}, ...]
            temperature: 温度参数，控制回复的随机性，范围0-1
            
        Returns:
            str: 模型的回复内容
        """

        # 这里需要使用正则表达式进行解析，如果message当中有```json，那么就按照json格式进行解析，否则就按照普通文本进行解析
        # 如果message当中有```json，那么就按照json格式进行解析，否则就按照普通文本进行解析
        for message in messages:
            if "```json" in message["content"]:
                message["content"] = json.loads(message["content"]) 

        return await self.llm.chat(
            messages=messages,
            temperature=temperature
        )

