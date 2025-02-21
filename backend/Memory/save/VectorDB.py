from typing import List, Dict, Any, Union
import importlib
from pydantic import BaseModel

# 配置类
class VectorDBConfig(BaseModel):
    db_type: str = "chromadb"  # 可选 chromadb | lancedb
    db_path: str = "vector_storage"
    embedding_dim: int = 1024

# 统一接口定义
class IVectorDB:
    """向量数据库统一接口"""
    
    def create_collection(self, name: str) -> Any:
        """创建集合/表"""
        raise NotImplementedError
        
    def delete_collection(self, name: str) -> bool:
        """删除集合/表"""
        raise NotImplementedError
        
    def add_data(self, collection: Any, data: Dict) -> bool:
        """添加数据
        data结构: {
            "id": Union[int, str],
            "vector": List[float],
            "text": str,
            "metadata": Dict
        }
        """
        raise NotImplementedError
        
    def query_vector(self, collection: Any, vector: List[float], top_k: int=3) -> List[Dict]:
        """向量相似查询"""
        raise NotImplementedError
        
    def query_metadata(self, collection: Any, filters: Dict) -> List[Dict]:
        """元数据查询"""
        raise NotImplementedError
        
    def update_data(self, collection: Any, data_id: Union[int, str], new_data: Dict) -> bool:
        """更新数据"""
        raise NotImplementedError
        
    def delete_data(self, collection: Any, data_id: Union[int, str]) -> bool:
        """删除数据"""
        raise NotImplementedError
        
    def name_to_pinyin(self, text: str) -> str:
        """名称转拼音格式"""
        raise NotImplementedError
        
    def list_collections(self) -> List[str]:
        """列出所有集合/表"""
        raise NotImplementedError
        
    def time_search(self, collection: Any, timestamp: int) -> List[Dict]:
        """时间范围查询"""
        raise NotImplementedError
        
    def id_search(self, collection: Any, data_id: Union[int, str]) -> Dict:
        """ID精确查询"""
        raise NotImplementedError
        
    def data_upsert(self, collection: Any, data: Dict) -> bool:
        """数据更新插入"""
        raise NotImplementedError

# 数据库工厂
class VectorDBFactory:
    @staticmethod
    def create_db(config: VectorDBConfig) -> IVectorDB:
        """根据配置创建数据库实例"""
        if config.db_type == "chromadb":
            module = importlib.import_module("backend.Memory.Chromadb_Manager")
            return ChromaDBAdapter(module.ChromaDBManager(config.db_path))
        elif config.db_type == "lancedb":
            module = importlib.import_module("backend.Memory.LanceDB_Manager")
            return LanceDBAdapter(module.LanceDBManager(config.db_path))
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")

# ChromaDB适配器
class ChromaDBAdapter(IVectorDB):
    def __init__(self, chroma_db):
        self.db = chroma_db
        
    def create_collection(self, name: str) -> Any:
        return self.db.open_or_create_collection(name)
        
    def add_data(self, collection: Any, data: Dict) -> bool:
        return self.db.add_data(
            collection=collection,
            id=data["id"],
            vector=data["vector"],
            text=data["text"],
            category=data["metadata"].get("category")
        )
        
    def query_vector(self, collection: Any, vector: List[float], top_k: int=3) -> List[Dict]:
        results = self.db.vector_search(collection, vector, limit=top_k)
        return [{"text": text, "score": score} for text, score in results]

    def name_to_pinyin(self, text: str) -> str:
        return self.db.name_to_pinyin(text)
        
    def list_collections(self) -> List[str]:
        return [col.name for col in self.db.client.list_collections()]
        
    def time_search(self, collection: Any, timestamp: int) -> List[Dict]:
        return collection.query(
            query_texts=[""],
            where={"id": {"$gt": timestamp}}
        )['documents'][0]
        
    def id_search(self, collection: Any, data_id: Union[int, str]) -> Dict:
        result = collection.get(ids=[str(data_id)])
        return {
            "text": result['documents'][0],
            "metadata": result['metadatas'][0]
        }
        
    def data_upsert(self, collection: Any, data: Dict) -> bool:
        metadata = data.get("metadata", {})
        return collection.upsert(
            ids=[str(data["id"])],
            embeddings=[data["vector"]],
            documents=[data["text"]],
            metadatas=[metadata]
        )

# LanceDB适配器
class LanceDBAdapter(IVectorDB):
    def __init__(self, lance_db):
        self.db = lance_db
        
    def create_collection(self, name: str) -> Any:
        return self.db.open_or_create_table(name)
        
    def add_data(self, collection: Any, data: Dict) -> bool:
        return self.db.add_data(
            table=collection,
            id=data["id"],
            vector=data["vector"],
            text=data["text"],
            metadata=data["metadata"]
        )

    def name_to_pinyin(self, text: str) -> str:
        return self.db.name_to_pinyin(text)
        
    def list_collections(self) -> List[str]:
        return self.db.db.table_names()
        
    def time_search(self, collection: Any, timestamp: int) -> List[Dict]:
        return collection.search().where(f"id > {timestamp}").to_list()
        
    def id_search(self, collection: Any, data_id: Union[int, str]) -> Dict:
        return collection.search().where(f"id = {data_id}").to_list()[0]
        
    def data_upsert(self, collection: Any, data: Dict) -> bool:
        return collection.add([{
            "id": data["id"],
            "vector": data["vector"],
            "text": data["text"],
            **data.get("metadata", {})
        }])

# 配置示例
db_config = VectorDBConfig(db_type="chromadb")

# 初始化示例
vector_db = VectorDBFactory.create_db(db_config)

