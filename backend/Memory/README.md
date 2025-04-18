## 核心功能
1. **记忆存储**：将对话、经历等信息向量化存储
2. **记忆检索**：基于语义相似度的快速检索
3. **上下文管理**：维护对话上下文
4. **元数据管理**：支持基于时间、类型等元数据的过滤



## 1. 集合管理重构
使用动态集合管理（私聊按朋友姓名，群聊按群名）
每个集合使用时间戳作为消息ID
每个私聊集合包含一个以朋友姓名为ID的个人信息文档

## 2. 存储逻辑优化
添加消息时直接存入对应集合

## 3. 每日总结改进
凌晨2点遍历所有私聊集合,只处理当天的原始消息
更新个人信息文档（使用朋友姓名为ID）

## 4. 查询优化
直接通过朋友/群名定位集合

## 5. 上下文保存验证
在add_conversation中确保先保存旧上下文再添加新消息
使用current_context维护当前对话的临时上下文

. 安全查询：查询时优先使用内存中的集合，不存在时直接从持久化存储加载
3. 可靠遍历：每日清理改为直接从客户端获取集合列表，不依赖内存中的字典
4. 错误处理：添加更完善的异常捕获和处理


## 代码说明：
1. 自定义嵌入函数：
AliyunMultimodalEmbedding类继承自LanceDB的EmbeddingFunction
支持文本和图片两种输入类型（自动检测）
调用阿里云API时自动处理Base64编码

2. 多模态数据模型：
使用Pydantic模型定义数据结构
包含内容类型（文本/图片）、元数据字段
自动向量化存储

3. 数据库管理功能：
表创建/管理
多模态数据增删查
支持文本和图像的混合搜索
数据统计和状态查询

4. 测试用例：
文本和图像数据的添加
跨模态搜索（用文本搜图片、用图片搜图片）
数据删除验证
表结构查看

### 使用前需要：
1. 安装依赖：pip install lancedb requests python-dotenv
2. 准备测试图片目录test_images
根据实际API端点调整EMBEDDING_ENDPOINT
此实现完整覆盖了LanceDB的核心API，并针对多模态场景进行了扩展，可直接作为数据库管理模块集成到应用中。