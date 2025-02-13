import dashscope
from dashscope import Generation
from typing import List, Dict, Optional
import asyncio
import json

class AliyunLLM:
    def __init__(self, api_key: str, model_version: str = "qwen-max-2025-01-25"):
        """
        初始化阿里云通义千问API客户端
        
        Args:
            api_key: 阿里云API密钥
            model_version: 模型版本，默认使用qwen-max
        """
        self.api_key = api_key
        self.model_version = model_version
        dashscope.api_key = api_key

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        调用通义千问进行对话

        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "你好"}, ...]
            temperature: 温度参数，控制回复的随机性，范围0-1
            max_tokens: 最大生成token数
            stream: 是否使用流式响应

        Returns:
            str: 模型的回复内容
        """
        try:
            response = await asyncio.to_thread(
                Generation.call,
                model=self.model_version,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or 1500,
                result_format='message',  # 返回格式为消息格式
                stream=stream
            )
            
            if response.status_code == 200:
                # 检查是否为流式响应
                if stream:
                    full_response = ""
                    for chunk in response:
                        if chunk.output and chunk.output.choices:
                            content = chunk.output.choices[0].message.content
                            full_response += content
                    return full_response
                else:
                    return response.output.choices[0].message.content
            else:
                error_msg = f"API调用失败: {response.code} - {response.message}"
                raise Exception(error_msg)
                
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
            response = await asyncio.to_thread(
                Generation.call,
                model=self.model_version,
                prompt=text,
                task='embeddings'  # 使用嵌入任务
            )
            
            if response.status_code == 200:
                return response.output.embeddings
            else:
                raise Exception(f"获取嵌入向量失败: {response.code} - {response.message}")
                
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

# 使用示例
async def test_chat():
    # 从配置文件加载API密钥
    import yaml
    with open("config/settings.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    api_key = config["llm"]["params"]["ali_qwen"]["api_key"]
    model_version = config["llm"]["params"]["ali_qwen"]["version"]
    
    # 初始化LLM客户端
    llm = AliyunLLM(api_key=api_key, model_version=model_version)
    
    # 测试对话
    messages = [
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ]
    
    try:
        response = await llm.chat(messages=messages)
        print("AI回复:", response)
    except Exception as e:
        print("错误:", str(e))

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_chat()) 