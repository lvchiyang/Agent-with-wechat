以下是关于 ChromaDB 的使用文档梳理，涵盖了安装、基本操作和使用场景等内容：
1. ChromaDB 简介
ChromaDB 是一个开源的向量数据库，专门用于存储和检索高维向量数据。它具有以下特点：
轻量级：易于安装和使用，适合快速开发。
与生成式 AI 无缝集成：能够高效管理文本嵌入和相似度搜索。
灵活的存储选项：支持内存存储、持久化存储以及客户端/服务器模式。
2. 安装 ChromaDB
通过以下命令安装 ChromaDB：

pip install chromadb
如果在安装过程中遇到问题，可能是因为依赖的 chroma-hnswlib 需要 C++ 编译器和 CMake。建议安装 Visual Studio Build Tools 并确保勾选 C++ 编译器和 CMake。
3. 创建 ChromaDB 客户端
ChromaDB 提供了多种客户端创建方式：
3.1 内存客户端
数据存储在内存中，程序结束后数据丢失：

import chromadb
client = chromadb.Client()
3.2 持久化客户端
将数据持久化到指定路径：

client = chromadb.PersistentClient(path="/path/to/save/to")
如果路径不存在，会自动创建。
3.3 客户端/服务器模式
首先启动 Chroma 服务：

chroma run --path db_path
然后创建客户端：

chroma_client = chromadb.HttpClient(host='localhost', port=8000)
4. 创建 Collection
Collection 是存储嵌入、文档和元数据的地方。创建 Collection 的代码如下：

collection = client.create_collection(name="my_collection")
Collection 的名称必须满足以下规则：
长度在 3-63 个字符之间。
以小写字母或数字开头和结尾，中间可以包含点、破折号、下划线。
5. 基本操作
5.1 添加数据
向 Collection 中添加文本数据：

collection.add(
    documents=["This is a document about pineapple", "This is a document about oranges"],
    ids=["id1", "id2"]
)
5.2 查询数据
通过查询文本检索最相似的结果：

results = collection.query(
    query_texts=["This is a query document about hawaii"],
    n_results=2
)
print(results)
查询结果会返回最相似的文档及其 ID 和距离。
5.3 删除数据
通过 ID 删除数据：

collection.delete("id1")
5.4 更新数据
更新指定 ID 的文档内容：

collection.update(ids=["id2"], documents=["Updated document about oranges"])
6. 其他操作
6.1 检查心跳
检查 ChromaDB 服务是否正常运行：

client.heartbeat()
6.2 列出所有 Collection

client.list_collections()
7. 使用场景
ChromaDB 适用于以下场景：
NLP 项目：管理文本嵌入和语义搜索。
嵌入管理：存储和检索高维向量数据。
快速原型开发：轻量级且易于上手。
8. 官方文档
更多详细信息和高级功能可以参考 ChromaDB 的官方文档：https://docs.trychroma.com/docs/overview/introduction。
希望这份文档能帮助你快速上手 ChromaDB！


## 使用自定义嵌入向量存取数据的示例
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer

# 加载本地模型
model = SentenceTransformer('path/to/your/model')

class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, texts: Documents) -> Embeddings:
        # 使用自定义模型生成嵌入向量
        embeddings = model.encode(texts)
        return embeddings.tolist()

# 创建 ChromaDB 集合并指定嵌入函数
client = chromadb.Client()
collection = client.create_collection(
    name="my_collection",
    embedding_function=MyEmbeddingFunction()
)