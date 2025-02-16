import os
import json  # 添加json库用于序列化
import pytz
import logging
import asyncio
import lancedb
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
from backend.Memory.LanceDB_Manager import LanceDBManager

'''
请注意，修改代码的时候，不要动这篇代码里的注释
'''

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置 LanceDB 存储路径
lance_path = Path("backend/Memory/Agent1_LanceDB")
os.makedirs(lance_path, exist_ok=True)

'''
context的对话格式
{
    "id": id,  # 时间戳
    "category": 私聊/群聊
    "friend_name": friend_name # 朋友/user姓名
    "group_name": group_name # 群聊名称，可为空
    "Dialogue": "friend_name:   assitant: "  # 对话内容
    "image": image,  # 暂且不支持图片信息
} 

上下文格式，最近几条对话的一个列表


前端发来的message的数据格式
{
    "id": id,  # 时间戳
    "category": 私聊/群聊
    "friend_name": friend_name # 朋友/user姓名
    "group_name": group_name # 群聊名称，可为空
    "text": text  # 对话内容
    "image": image,  # 图片信息，为空
} 
'''

class MemoryManager:
    def __init__(self, LLMClient):
        self.LLMClient = LLMClient
        self.lance_db = LanceDBManager()
        # 移除非线程安全的事件循环代码
        self.last_interacted = {"friend_name": None, "group_name": None}
        self.context: List[Dict] = []
        self.friend_daily_tasks = {}
    
    def _get_table(self, table_name: str) -> lancedb.table.Table: # 通过名，返回一个table对象
        """统一表管理方法"""
        # 自动创建不存在的表
        if table_name not in self.lance_db.list_tables():
            # 使用LLM生成初始嵌入向量
            self.lance_db.create_table(
                table_name = table_name, # 所有的表都按对话对象的名称存取
                id = "profile" , # 将个人信息的id设置为profile
                vector="",
                text="",
                image="",
                category=""
            )
        return self.lance_db.open_table(table_name)
    
    def new_message(self, message: str) -> str:
        """处理新消息，提供上下文"""
        current_friend = message["friend_name"]
        current_group = message.get("group_name", "")
        
        if self.last_interacted["friend_name"] != current_friend or \
           self.last_interacted["group_name"] != current_group:
            if len(self.context) > 0:
                context_to_archive = self.context.copy()  # 创建上下文副本
                self._archive_context(context_to_archive, message)
                self.context.clear()
                logger.info(f"检测到新对话者: {current_friend}@{current_group}，已保存上下文")
                
            self.last_interacted = {
                "friend_name": current_friend,
                "group_name": current_group
            }
            return None
        else:
            return self.context

    def query_context(self, message: str = None) -> List[Dict]:
        """增强版上下文查询"""
        try:
            # 自动选择对应的表
            table_name = message["friend_name"] if message["category"] == "私聊" else message["group_name"]

            # 检查表是否存在
            if table_name not in self.lance_db.list_tables():
                return [{"text": "记忆中尚且没有相关信息"}]
            else:
                table = self._get_table(table_name)
            
                # 生成查询向量
                query_embedding = self.LLMClient.get_embedding(message) if message else [0.0]*1024
                
                # 执行向量搜索
                return self.lance_db.vector_search(
                    table=table,
                    query_vector=query_embedding,
                    limit=5
                )
            
        except Exception as e:
            logger.error(f"上下文查询失败: {str(e)}")
            return []

    '''
    add_conversation需要实现的功能
    将前端发来的message和assitant的回答answer，处理成context的对话格式，然后插入到context[]中
    判断context[]的长度，如果超过10条，则将context[]中的旧的7条对话记录编码后存入数据库，然后删除context[]中的前7条对话记录

    需要考虑embedding模型的tokens限制，5条对话记录，作为一个记忆的单元，进行存储，多了就要被截断了
    '''
    def add_conversation(self, message: dict, answer: str):
        """添加对话记录（完整实现）"""
        try:
            # 添加日志记录
            logger.debug(f"开始添加对话记录: message={message}, answer={answer}")

            # 构建对话记录
            structured_data = {
                "id": str(datetime.now().timestamp()),
                "category": message["category"],
                "friend_name": message["friend_name"],
                "group_name": message.get("group_name", ""),
                "Dialogue": f"{message['friend_name']}: {message['text']}\nAssistant: {answer}",
                "image": ""  #  message.get("image", "") # 暂且不支持图片信息
            }
            
            # 添加上下文
            self.context.append(structured_data)
            
            # 上下文归档逻辑
            if len(self.context) > 8:
                context_to_archive = self.context[:5].copy()
                # 保留最近3条上下文
                self.context = self.context[-3:]
                self._archive_context(context_to_archive, message)
            
            # 添加日志记录
            logger.info(f"成功添加对话记录")
            return True
        except Exception as e:
            logger.error(f"添加对话失败: {str(e)}")
            return False

    def _archive_context(self, context: List[Dict], message: dict):
        """上下文归档（适配 LanceDB）"""
        try:
            # 将上下文列表转换为JSON字符串
            context_str = json.dumps(context, ensure_ascii=False)
            
            # 生成嵌入向量
            embedding = self.LLMClient.get_embedding(context_str)  # 现在传入的是字符串
            
            # 自动选择对应的表
            table_name = message["friend_name"] if message["category"] == "私聊" else message["group_name"]
            table = self._get_table(table_name)
            
            # 构建存储数据
            data = {
                "id": str(datetime.now().timestamp()),
                "vector": embedding,
                "text": context_str,  # 存储原始对话结构
                "image": "",
                "category": message["category"],
            }

            # 插入数据库
            self.lance_db.add_data(table, **data)
            
            # 新增数据之后，新增索引
            if self.lance_db.get_table_count(table) < 100:
                self.lance_db.create_vector_index_1(table)
            else:
                # 自动创建高级索引方式
                self.lance_db.create_vector_index_100(table)
        except Exception as e:
            logger.error(f"上下文归档失败: {str(e)}")


    # async def daily_cleanup(self):
    #     """每日维护任务"""
    #     while True:
    #         await asyncio.sleep(86400)  # 24小时

    #         # 遍历所有表进行维护
    #         for table_name in self.lance_db.list_tables():
    #             table = self.lance_db.db.open_table(table_name)
    #             # 清理过期数据（示例保留30天内数据）
    #             table.delete(f"metadata['timestamp'] < '{datetime.now() - timedelta(days=30)}'")

    #         logger.info("每日维护任务完成")


    async def daily_summary(self):
        tables = self.lance_db.list_tables()
        for table_name in tables:
            await self._info_summary(table_name)

    async def _info_summary(self, friend_name: str):
        """信息总结更新"""
        table = self._get_table(friend_name)
        
        # 查询当天数据
        today = datetime.now().date().isoformat()
        results = table.search([0.0]*1024).where(
            f"id >= '{today}'"
        ).execute()
        
        if len(results) == 0:  # 修改为检查结果长度，因为LanceDB返回的是列表而不是DataFrame
            return

        # 获取个人信息
        profile_results = table.search([0.0]*1024).where("id == 'profile'").execute()
        profile = profile_results[0]['text'] if len(profile_results) > 0 else "无已知信息"  # 提取profile文本内容

        # 生成总结提示
        prompt = f"""请从今日与{friend_name}的对话中提取重要个人信息：        
        要求：
        1. 只返回个人相关信息，不要输出其他无关内容，内容保持简洁，回答中不需要对你的更改做任何说明
        2. 为今日总结的信息添加时间戳标签用来区分信息的时间
        3. 如果今日没有对话记录，则将已知信息返回
        4. 不要丢失之前的已知信息，除非相同的内容产生更新

        已知信息：{profile}
        今日对话记录：{[result['text'] for result in results]}
        """
        
        try:
            response = await self.LLMClient.chat(prompt)
            # 更新个人信息
            self.lance_db.update_data(
                table,
                where_condition="id == 'profile'",  # 修改为更新profile记录
                values={"text": response, "category": "private_context"}
            )
        except Exception as e:
            logger.error(f"每日总结失败: {str(e)}")
