import chromadb
import numpy as np
from typing import List, Dict, Optional
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from pypinyin import pinyin, Style
import logging

logger = logging.getLogger(__name__)

class RandomEmbedding(EmbeddingFunction):
    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        
    def __call__(self, texts: Documents) -> Embeddings:
        """生成随机嵌入向量"""
        return [
            np.random.rand(self.dimension).tolist()
            for _ in range(len(texts))
        ]

class ChromaDBManager:
    def __init__(self, path: str, embedding_dim: int = 1024):
        """初始化数据库连接"""
        self.client = chromadb.PersistentClient(path=path)
        self.embedding_fn = RandomEmbedding(dimension=embedding_dim)
        self.collection = None
        self.current_collection_name = None

    def name_to_pinyin(self, text):
        # 使用pypinyin进行转换，普通风格
        result = pinyin(text, style=Style.NORMAL,heteronym=False)
        # 提取拼音并首字母大写，不加空格
        pinyin_str = "".join([item[0].capitalize() for item in result])
        pinyin_str = pinyin_str.replace(" ", "")
        return pinyin_str
    
    # 由客户端，管理集合
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return self.client.list_collections()

    def open_or_create_collection(self, name: str) -> chromadb.Collection:
        """获取集合对象"""
        return self.client.get_or_create_collection(name, embedding_function=self.embedding_fn)

    # 配置相似度计算方式
    def create_collection(self, name: str, metadata: Dict = None) -> None:
        """创建集合"""
        name = self.name_to_pinyin(name)    
        # 添加默认元数据
        if not metadata:
            metadata = {"hnsw:space": "cosine"}  # 添加默认的相似度计算方式
        
        self.collection = self.client.create_collection(
            name=name,
            metadata=metadata
        )

    '''
    删除集合，但是原文件还都在，就是list_collections()中没有
    需要手动删除文件夹
    如果不删除的话，下次确实能找到
    '''
    def delete_collection(self, name: str) -> None:  
        """删除集合"""
        name = self.name_to_pinyin(name)    
        self.client.delete_collection(name)
    
    # 以下都是一个集合内部的操作，对文档的操作，主语是集合    
    def add_data(self, collection: chromadb.Collection, id: int, vector: List[float], 
                text: str, category: str = "") -> None:
        """添加多维数据（兼容LanceDB的add_data）"""

        metadata = {"category": category, "id": id}
        # 检查collection是否存在
        collection.add(
            ids=[f"{id}"],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata]
        )

    def vector_search(self, collection: chromadb.Collection, query_vector: List[float], 
                     filter: Dict = None, limit: int = 3) -> list[str]: 
        
        """向量相似性搜索（对应LanceDB的vector_search）"""
        try:
            results = collection.query(
                query_embeddings=[query_vector],
                where=filter,
                n_results=limit
            )
            # 添加安全访问
            return results['documents'][0] if results and results.get('documents') else []
        except (IndexError, KeyError) as e:
            logger.warning(f"向量搜索返回空结果: {str(e)}")
            return []
    
    def time_search(self, collection: chromadb.Collection, timestamp: int = None) -> list[str]:
        try:
            results = collection.query(
                query_texts=[""],
                where={"id": {"$gt": timestamp}},
            )
            # 添加空结果处理
            return results['documents'][0] if results and results['documents'] else []
        except (IndexError, KeyError) as e:
            logger.warning(f"时间查询返回空结果: {str(e)}")
            return []
    
    def id_search(self, collection, id: int):
        try:
            results = collection.get(ids=[str(id)])
            # 增强空值检查
            if not results or not results.get("documents") or len(results["documents"]) == 0:
                return None
            
            # 添加metadata存在性检查
            metadata = results.get("metadatas", [{}])[0] if results.get("metadatas") else {}
            return {
                "category": metadata.get("category", ""),
                "text": results["documents"][0]
            }
        except IndexError as e:
            logger.error(f"ID查询索引越界: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"ID查询失败: {str(e)}")
            return None

    def id_search_list(self, collection: chromadb.Collection, id: int = 1) -> list[str]:
        """个人信息"""
        results = collection.get(
            ids=[f"{id}"]
        )
        return results['documents']

    def data_upsert(self, collection: chromadb.Collection, id: int = 1, vector: List[float] = None, 
                text: str = "暂时没有信息", category: str = "") -> None:
        metadata = {"category": category}
        
        """更新数据（需要确认ChromaDB的更新方式）"""
        # ChromaDB的更新可能需要通过upsert实现
        collection.upsert(
            ids=[f"{id}"], # 默认个人信息的文档id为1
            embeddings = [vector],
            documents = [text],
            metadatas = [metadata]
        )

    def delete_data(self, collection: chromadb.Collection, id: int) -> None:  # 现在不好使。。
        """删除集合中的数据"""
        collection.delete(ids=[f"{id}"])

def test_chromadb_manager():
    path = "Agnet_ChromDB"

    chroma_db = ChromaDBManager()
    print("已有集合",chroma_db.list_collections())
    
    try:
        # 测试集合创建
        test_collection = "nihao"
        coll = chroma_db.open_or_create_collection(test_collection)
        print("创建集合",chroma_db.list_collections())
        
        
        # 测试添加数据
        test_id = 1
        test_vector = [0.1] * 1024  # 示例向量
        chroma_db.add_data(
            collection=coll,
            id=test_id,
            vector=test_vector,
            text="测试文本",
            category="测试分类"
        )
        
        # 测试向量搜索
        results = chroma_db.vector_search(coll, test_vector, limit=1)
        print("向量搜索",results)

        search_results = chroma_db.time_search(coll, timestamp = 0)
        print("时间搜索",search_results)

        test_id = 0
        test_vector = [0.1] * 1024  # 示例向量
        chroma_db.add_data(
            collection=coll,
            id=test_id,
            vector=test_vector,
            text="测试文本",
            category="测试分类"
        )
        # 测试个人信息搜索
        search_results = chroma_db.id_search(coll, 0)
        print("个人信息搜索",search_results)
        
        # 测试个人信息更新
        chroma_db.data_upsert(
            collection=coll,
            vector=[0.2]*1024,
            text="更新文本"
        )
        search_results = chroma_db.id_search(coll, 0)
        print("个人信息更新",search_results)

        print("所有集合",chroma_db.list_collections())

        # 测试删除
        chroma_db.delete_data(coll, 1)
        id_search = chroma_db.id_search(coll, 0)
        print("删除后搜索",id_search)

        # 索引原文
        _id_search_list = chroma_db.id_search_list(coll, 0)
        print("索引原文",_id_search_list)


        # chroma_db.delete_collection(name = test_collection)
        # print("测试集合已删除",chroma_db.list_collections())

        print("所有测试通过!")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    test_chromadb_manager()



