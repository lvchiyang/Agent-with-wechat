import sys
from pathlib import Path
import yaml
from typing import List, Dict, Optional, Union
import asyncio
from backend.LLM.AliyunLLM import AliyunLLM
from backend.LLM.prompt_manager import PromptManager
import platform
import logging

logger = logging.getLogger(__name__)
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

# 添加项目根目录到sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

class LLM_Client:
    def __init__(self):
        self.llm = None
        self.prompt_manager = PromptManager()
        self._load_config()

    def _load_config(self):
        # 获取项目根目录
        BASE_DIR = Path(__file__).resolve().parent.parent

        # 加载配置
        config_path = BASE_DIR / "config" / "settings.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 初始化大模型（包含嵌入功能）
        self.llm = AliyunLLM(
            config["llm"]["params"]["ali_qwen"]  # 直接传入整个配置字典
        )

    async def chat(
        self,
        system_prompt: str = "你是一个AI助手，你的任务是根据用户的问题给出回答。",
        user_input: str = "",
        enable_search: bool = False,
        response_format: Optional[Dict] = {"type": "text"}
    ) -> str:
        """
        调用大模型进行对话
        
        Args:
            user_input: 用户输入内容
            enable_search: 是否启用联网搜索
            system_prompt: 系统提示词，默认为"你是一个有帮助的AI助手。"
            response_format: 响应格式配置，例如 {"type": "json_object"}
            
        Returns:
            str: 模型的回复内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        response = await self.llm.chat(
            messages=messages,
            enable_search=enable_search,
            response_format=response_format
        )
        # logger.info(f"LLM调用成功，响应内容: {response}")

        return response

    def get_embedding(self, input_data: Union[str, bytes]) -> List[float]:
        """获取文本或图片的嵌入向量"""
        return self.llm.generate_embeddings(input_data)

# 使用示例
async def test_chat():
    # 初始化LLM客户端
    llm_client = LLM_Client()
    
    system_prompt = "你是一个有帮助的AI助手。"
    # 测试对话
    user_input = "中国队在亚冬会获得了多少枚金牌"
    
    try:
        # 测试文本嵌入
        text_embedding = llm_client.get_embedding(user_input)
        print(f"测试文本: {user_input}")
        print(f"生成的向量: {text_embedding}")
        print(f"向量维度: {len(text_embedding)}")

        # 测试对话功能
        response = await llm_client.chat(
            system_prompt=system_prompt, 
            user_input=user_input, 
            enable_search=True
        )
        print("AI回复:", response)
        
    except Exception as e:
        print("错误:", str(e))

if __name__ == "__main__":
    # 运行测试
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_chat())