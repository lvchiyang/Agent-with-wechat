import sys
from pathlib import Path
import os

from pypinyin import pinyin, Style


# 将项目根目录添加到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# 使用绝对导入
from backend.LLM.LLM_Client import LLM_Client
from datetime import datetime
import time
import json


import lancedb
import numpy as np
from typing import List, Dict, Optional

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 设置 ChromaDB 存储路径
chroma_path =  "backend/Memory/lancedb_data"
os.makedirs(chroma_path, exist_ok=True)  # 确保目录存在

class LanceDBManager:
    def __init__(self, uri: str = str(chroma_path)):
        """初始化数据库连接"""
        self.db = lancedb.connect(uri)

    def name_to_pinyin(self, text):
        # 使用pypinyin进行转换，普通风格
        result = pinyin(text, style=Style.NORMAL,heteronym=False)
        # 提取拼音并首字母大写，不加空格
        pinyin_str = "".join([item[0].capitalize() for item in result])
        return pinyin_str
        
    def create_table(self, table_name: str, id: str = "", vector: List[float] = [0.0] * 1024, text: str = "", image: str = None, category: str = None) -> lancedb.table.Table:
        table_name = self.name_to_pinyin(table_name)
        """创建表并插入初始数据"""
        data = [
            {
                "id": id,  # 时间戳/姓名
                "vector": vector,  # 1024维向量
                "text": text,
                "image": image, 
                "category": category,  # 预留
            } 
        ]
        return self.db.create_table(table_name, data, mode="overwrite")
    
    def open_table(self, table_name: str) -> lancedb.table.Table:
        table_name = self.name_to_pinyin(table_name)
        """打开表"""
        return self.db.open_table(table_name)   
    
    def get_table_count(self, table: lancedb.table.Table) -> int:
        """获取表数据量"""
        return table.count_rows()
    
    def close_table(self, table: lancedb.table.Table) -> None:
        """关闭表"""
        table.close()

    def add_data(self, table: lancedb.table.Table, id: str, vector: List[float], text: str, image: str = None):
        """插入新数据"""
        data = [
            {
                "id": id,  # 时间戳/姓名
                "vector": vector,  # 1024维向量
                "text": text,
                "image": image, 
            } 
        ]
        return table.add(data)
    
    def delete_data(self, table: lancedb.table.Table, where_condition: str) -> None:
        """删除数据"""
        table.delete(where=where_condition)

    def update_data(self, table: lancedb.table.Table, where_condition: str, values: Dict) -> None:
        """更新数据"""
        table.update(where=where_condition, values=values)

    def vector_search(self, table: lancedb.table.Table, query_vector: List[float], limit: int = 5, filter: Optional[str] = None) -> List[Dict]:
        """向量相似度搜索"""
        query = table.search(query_vector).limit(limit).to_pandas()
        text_list = query["text"].tolist()
        return text_list
    
    '''
    不同索引方式
    向量索引方式和标量索引方式，一个表只能存在一种，可以在向量索引中，使用标量索引过滤，
    好像不支持动态扩建数据库，因为数据变化，就需要重新构建索引。
    如果动态扩展数据库，就需要重新创建索引    
    '''
    def create_vector_index_1(self, table: lancedb.table.Table, index_type_set: str = "IVF_FLAT", num_partitions_set: int = 1, num_sub_vectors_set: int = 64) -> None:
        """创建索引，只设置一个分区"""
        table.create_index(vector_column_name = "vector", 
                           metric = "cosine",  # cosine/L2/dot
                           index_type = index_type_set, 
                           num_partitions = num_partitions_set, 
                           num_sub_vectors=num_sub_vectors_set, 
                           replace=True)
    
    def create_vector_index_100(self, table: lancedb.table.Table, index_type_set: str = "IVF_FLAT", num_partitions_set: int = 10, num_sub_vectors_set: int = 64) -> None:
        """创建大量数据集时候的索引方法"""
        table.create_index(vector_column_name = "vector", 
                           metric = "cosine",  # cosine/L2/dot
                           index_type = index_type_set, 
                           num_partitions = num_partitions_set, 
                           num_sub_vectors=num_sub_vectors_set, 
                           replace=True)

    def create_scalar_index(self, table: lancedb.table.Table, column: str, index_type: str = "BTREE") -> None:
        """创建标量索引"""
        table.create_scalar_index(column, index_type=index_type, replace=True)
    
    def list_tables(self) -> List[str]:
        """列出所有表"""
        return self.db.table_names()

    def delete_table(self, table_name: str) -> None:
        table_name = pinyin(table_name, heteronym=False)
        """删除表"""
        self.db.drop_table(table_name)


    

def test_vector_search():
    db_manager = LanceDBManager()

    # 创建测试表
    test_vector = np.random.rand(1024).tolist()
    test_table = db_manager.create_table("test_table2", "1", test_vector, "测试文本")
    print("创建表成功，表列表:", db_manager.list_tables())

    # 打开表
    test_table = db_manager.open_table("test_table2")

    
    # 插入新数据
    new_vector = np.random.rand(1024).tolist()
    db_manager.add_data(test_table, "2", new_vector, "新插入文本")
    print("数据插入成功")
    
    # 执行搜索
    query_vec = np.random.rand(1024).tolist()
    results = db_manager.vector_search(test_table, new_vector, limit=3)
    print("搜索结果示例:", results)
    
    # 更新数据
    db_manager.update_data(test_table, "id == '1'", {"text": "更新后的文本"})
    print("数据更新成功")
    
    # 删除数据
    db_manager.delete_data(test_table, "id == '1'")
    print("数据删除成功")
    
    # 创建索引
    db_manager.create_vector_index_1(test_table)
    print("索引创建成功")
    
    # 创建标量索引
    db_manager.create_scalar_index(test_table, "id")
    print("标量索引创建成功")
    
    # 删除表
    # db_manager.delete_table("test_table")
    print("表删除成功，剩余表:", db_manager.list_tables())



def test_add_data():
    db_manager = LanceDBManager()

    db_manager.create_table("test_table")
    print("创建表成功，表列表:", db_manager.list_tables())

    LLMClient = LLM_Client()


    timestamp = time.time()
    readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    query = {
        "id": "1739704423283",
        "category": "私聊",
        "friend_name": "A",
        "group_name": "测试群组",
        "text": "我20岁了",
        "image": ""
    }
    answer = "你好年轻"

    # 构建对话记录
    structured_data = {
        "id": str(readable_time),
        "category": query["category"],
        "friend_name": query["friend_name"],
        "group_name": query.get("group_name", ""),
        "Dialogue": f"{query['friend_name']}: {query['text']} Assistant: {answer}",
        "image": ""  #  message.get("image", "") # 暂且不支持图片信息
    }
    context: List[Dict] = []
    context.append(structured_data)
    context.append(structured_data)
    context.append(structured_data)
    context.append(structured_data)
    
    # 将字典转换为json字符串
    # context_str = json.dumps(structured_data, ensure_ascii=False)

    # 也可以将list[dict]转换为json字符串
    context_str = json.dumps(context, ensure_ascii=False)

    # dialogue_embedding = np.random.rand(1024).tolist()
    dialogue_embedding = LLMClient.get_embedding(context_str)

    # 打开表
    test_table = db_manager.open_table("test_table")

    db_manager.add_data(test_table, readable_time, dialogue_embedding, context_str)

    query = {
        "id": "1739704423283",
        "category": "私聊",
        "friend_name": "A",
        "group_name": "测试群组",
        "text": "我多大了？",
        "image": ""
    }
    query_str = json.dumps(query, ensure_ascii=False)

    # query_embedding = np.random.rand(1024).tolist()
    query_embedding = LLMClient.get_embedding(query_str)

    test_table = db_manager.open_table("test_table")

    results = db_manager.vector_search(test_table, query_embedding, limit=3)

    # print(results)
    # print(type(results))

    json_object = json.loads(results[0])
    print(json_object)


# 测试代码
if __name__ == "__main__":
    test_add_data()
    # test_vector_search()