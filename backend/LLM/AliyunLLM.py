import os
import asyncio
from openai import AsyncOpenAI
import platform
from typing import List, Dict, Optional

class AliyunLLM:
    def __init__(self, api_key: str, model_version: str = "qwen-plus"):
        """
        初始化阿里云通义千问API客户端
        
        Args:
            api_key: 阿里云API密钥
            model_version: 模型版本，默认使用qwen-plus
        """
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model_version = model_version

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        enable_search: bool = False
    ) -> str:
        """
        调用通义千问进行对话

        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "你好"}, ...]
            temperature: 温度参数，控制回复的随机性，范围0-1
            max_tokens: 最大生成token数
            stream: 是否使用流式响应
            enable_search: 是否启用联网搜索

        Returns:
            str: 模型的回复内容
        """
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.model_version,
                temperature=temperature,
                max_tokens=max_tokens or 1500,
                stream=stream,
                extra_body={"enable_search": enable_search}  # 添加联网搜索配置
            )
            
            if stream:
                full_response = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            error_msg = f"调用通义千问API时发生错误: {str(e)}"
            raise Exception(error_msg)

    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入表示

        Args:
            text: 输入文本

        Returns:
            List[float]: 文本的向量表示
        """
        try:
            response = await self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"  # 使用嵌入模型
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"获取文本嵌入时发生错误: {str(e)}")

    def format_prompt(self, system: str, user_input: str) -> List[Dict[str, str]]:
        """
        格式化对话提示

        Args:
            system: 系统提示词
            user_input: 用户输入

        Returns:
            List[Dict[str, str]]: 格式化后的消息列表
        """
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_input}
        ]

