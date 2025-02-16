import os
import asyncio
from openai import AsyncOpenAI
import platform
from typing import List, Dict, Optional, Union
import base64
import requests

ALIYUN_API_KEY = "sk-ac6676f765124b9dafbf47a3cb9c99a9"
EMBEDDING_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
VECTOR_DIM = 1024

class AliyunLLM:
    def __init__(self, config: Dict):
        """
        初始化阿里云通义千问API客户端
        
        Args:
            config: 包含api_key和model_version的配置字典
        """
        if not config or "api_key" not in config or "version" not in config:
            raise ValueError("配置字典必须包含api_key和version")
            
        self.chat_client = AsyncOpenAI(
            api_key=config["api_key"],
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model_version = config["version"]
        self.api_key = config["api_key"]  # 用于嵌入API


    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        response_format = None,
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
            response = await self.chat_client.chat.completions.create(
                messages=messages,
                model=self.model_version,
                temperature=temperature,
                max_tokens=max_tokens or 1500,
                stream=stream,
                response_format = response_format,
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

    def generate_embeddings(self, input_data: Union[str, bytes]) -> list[float]:
        """调用阿里云多模态嵌入API生成嵌入向量"""
        headers = {
            "Authorization": f"Bearer {ALIYUN_API_KEY}",
            "Content-Type": "application/json"
        }

        # 构建请求体
        payload = {
            "model": "multimodal-embedding-v1"
,
            "input": {
                "contents": [self._build_content(input_data)]
            },
            "parameters": {}
        }

        try:
            response = requests.post(EMBEDDING_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            
            # 解析响应
            response_data = response.json()
            
            # 检查是否返回错误信息
            if 'code' in response_data:
                error_code = response_data.get('code', 'UnknownError')
                error_message = response_data.get('message', 'Unknown error occurred')
                raise RuntimeError(f"API返回错误: {error_code} - {error_message}")
                
            if 'output' not in response_data or 'embeddings' not in response_data['output']:
                raise ValueError("API响应缺少有效数据")
                
            # 返回第一个嵌入向量
            return response_data['output']['embeddings'][0]['embedding']
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"API响应解析失败: {str(e)}")

    def _build_content(self, input_data: Union[str, bytes]) -> Dict:
        """根据输入数据类型构建内容对象"""
        if isinstance(input_data, bytes):
            return {
                "image": f"data:image/jpeg;base64,{base64.b64encode(input_data).decode('utf-8')}"
            }
        else:
            return {
                "text": input_data
            }

if __name__ == "__main__":
    # 初始化阿里云嵌入模型
    embedding_fn = AliyunLLM()
    
    # 测试文本
    test_text = "这是一段测试语句"
    
    try:
        # 测试文本嵌入
        print("测试文本嵌入:")
        text_embedding = embedding_fn.generate_embeddings(test_text)
        print(f"测试文本: {test_text}")
        print(f"生成的向量: {text_embedding}")
        print(f"向量维度: {len(text_embedding[0])}")
        
        # # 测试图片嵌入
        # print("\n测试图片嵌入:")
        # with open("./backend/Memory/cat.jpg", "rb") as f:
        #     image_data = f.read()
        # image_embedding = embedding_fn.compute_query_embeddings(image_data)
        # print(f"图片文件: cat.jpg")
        # print(f"生成的向量: {image_embedding}")
        # print(f"向量维度: {len(image_embedding[0])}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")