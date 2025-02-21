import chromadb
import numpy as np
import time
from typing import List, Dict, Optional
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

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
    def __init__(self, path: str = "chroma_db", embedding_dim: int = 1024):
        """初始化本地随机嵌入数据库"""
        self.client = chromadb.PersistentClient(path=path)
        self.embedding_fn = RandomEmbedding(dimension=embedding_dim)
        self.collection = None
        self.current_collection_name = None

    def create_collection(self, name: str) -> None:
        """创建使用随机嵌入的集合"""
        self.collection = self.client.create_collection(
            name=name,
            embedding_function=self.embedding_fn
        )
        self.current_collection_name = name # 当前集合名称

    def add_documents(self, documents: List[str], ids: List[str], embeddings: List[List[float]] = None, metadatas: List[Dict] = None) -> None:
        """添加文档（自动生成随机嵌入）"""
        self.collection.add(
            documents=documents,    # 文档内容
            metadatas=metadatas,    # 文档元数据，可以为空，过滤时候用
            embeddings=embeddings,  # 文档嵌入，可以为空，可以指定vector，如果不指定，旧调用创建时候配置的函数
            ids=ids                # 文档ID
        )

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict:
        """执行相似性查询"""
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )

    def delete(self, ids: List[str]) -> None:
        """删除指定ID的文档"""
        self.collection.delete(ids=ids)

    def list_collections(self) -> List[str]:
        """列出所有集合名称"""
        return self.client.list_collections()

def test_random_embeddings():
    """测试随机嵌入功能"""
    # 使用临时路径避免数据残留
    import tempfile
    test_path = tempfile.mkdtemp()
    db = ChromaDBManager(path=test_path)
    
    try:
        # 确保集合不存在
        if "test_random" in db.list_collections():
            db.client.delete_collection("test_random")
            await asyncio.sleep(0.5)  # 等待删除完成
        
        # 创建测试集合
        db.create_collection("test_random")
        print("集合创建成功")
        
        # 添加测试数据
        docs = ["文档1", "文档2", "文档3"]
        db.add_documents(docs, [f"doc_{i}" for i in range(len(docs))])
        print("文档添加成功")
        
        # 执行查询
        results = db.query(["测试查询"], n_results=2)
        print("\n查询结果:")
        for i, doc in enumerate(results['documents'][0], 1):
            print(f"{i}. {doc}")
            
    finally:
        # 清理测试数据
        try:
            if "test_random" in db.list_collections():
                db.client.delete_collection("test_random")
                print("\n测试数据已清理")
        except Exception as e:
            print(f"清理失败: {str(e)}")
        # 删除临时目录
        import shutil
        shutil.rmtree(test_path, ignore_errors=True)

if __name__ == "__main__":
    test_random_embeddings()