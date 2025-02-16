import os
import base64
import requests
from typing import Union, List, Dict
from lancedb.embeddings import EmbeddingFunction

# 阿里云多模态嵌入模型配置
ALIYUN_API_KEY = "sk-ac6676f765124b9dafbf47a3cb9c99a9"
EMBEDDING_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
VECTOR_DIM = 1024

class AliyunMultimodalEmbedding(EmbeddingFunction):
    """阿里云多模态嵌入模型封装类"""
    name: str = "multimodal-embedding-v1"

    @property
    def ndims(self) -> int:
        """返回嵌入向量的维度"""
        return VECTOR_DIM


    def generate_embeddings(self, input_data: Union[str, bytes]) -> list[float]:
        """调用阿里云多模态嵌入API生成嵌入向量"""
        headers = {
            "Authorization": f"Bearer {ALIYUN_API_KEY}",
            "Content-Type": "application/json"
        }

        # 构建请求体
        payload = {
            "model": self.name,
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
    embedding_fn = AliyunMultimodalEmbedding()
    
    # 测试文本
    test_text = "这是一段测试语句"
    
    try:
        # # 测试文本嵌入
        # print("测试文本嵌入:")
        # text_embedding = embedding_fn.compute_query_embeddings(test_text)
        # print(f"测试文本: {test_text}")
        # print(f"生成的向量: {text_embedding}")
        # print(f"向量维度: {len(text_embedding[0])}")
        
        # 测试图片嵌入
        print("\n测试图片嵌入:")
        with open("./backend/Memory/cat.jpg", "rb") as f:
            image_data = f.read()
        image_embedding = embedding_fn.compute_query_embeddings(image_data)
        print(f"图片文件: cat.jpg")
        print(f"生成的向量: {image_embedding}")
        print(f"向量维度: {len(image_embedding[0])}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")