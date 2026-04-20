# Agent-with-WeChat

基于大模型的微信聊天 Agent。项目实现了消息接入、记忆检索、角色化回复和任务规划的完整闭环，可用于构建具备长期记忆能力的对话系统。

## 核心能力

- **微信消息接入**：通过 GeWeChat 回调接收消息，支持私聊与群聊（前缀触发）处理。
- **多入口交互**：提供 FastAPI + WebSocket 服务，可从微信通道或前端输入统一进入 Agent。
- **RAG 记忆增强**：对话向量化归档到 ChromaDB，并在回复前做相似记忆召回。
- **角色化回复**：支持角色设定、语气设定、上下文拼接与状态感知 Prompt 生成。
- **Plan 规划循环**：周期性调用 LLM 生成结构化计划，执行工作/休闲/总结等动作。
- **每日记忆总结**：按天提取关键对话信息并回写到记忆库，持续更新用户画像。

## 系统架构

```text
消息输入(微信回调/WebSocket)
        |
        v
   Agent.handle_message
        |
        +--> MemoryManager.new_message (上下文切换)
        +--> MemoryManager.query_context (相似记忆召回)
        +--> PromptManager.get_system_prompt / get_user_prompt
        +--> LLM_Client.chat
        +--> MemoryManager.add_conversation (对话归档)
```

并行后台任务：

- `Plan.plan_loop`：定时获取计划并更新 Agent 状态
- `MemoryManager.daily_summary`：按天总结并更新长期记忆

## 目录结构

```text
backend/
  Agent/                  # Agent 主流程与计划模块
  LLM/                    # 模型抽象层与具体实现（Aliyun/Qwen）
  Memory/                 # 记忆管理与向量数据库管理
  channel/                # 微信通道与 API/WebSocket 服务
  config/                 # 人设、模型、微信配置
frontend/
  src/                    # 前端消息交互示例
module_test/              # 模块测试脚本
Agent_hall.py             # 启动入口
```

## 快速开始

### 1) 安装依赖

```bash
pip install -r requirements.txt
```

### 2) 配置模型与通道

编辑以下配置文件：

- `backend/config/settings.yaml`：配置模型与 API Key
- `backend/config/gewe_config.yaml`：配置 GeWeChat 服务地址与回调地址
- `backend/config/persona_config.yaml`：配置角色人设与语气风格

### 3) 启动

在项目根目录执行：

```bash
python Agent_hall.py
```

### 4) 连接与交互

- 微信通道：确保 GeWeChat 服务可用并完成登录
- 前端调试：可使用 `frontend/` 下页面或通过 WebSocket 连接服务进行测试

## 关键模块说明

- `backend/Agent/Agent_class.py`  
  Agent 主线程：调度消息处理、调用 LLM、更新记忆，并与 API 服务/计划循环并行运行。

- `backend/Memory/memory_manager.py`  
  负责上下文缓存、对话归档、向量检索、每日总结。

- `backend/Memory/ChromaDB_Manager.py`  
  ChromaDB 的集合管理、向量写入、检索和更新封装。

- `backend/LLM/LLM_Client.py`  
  统一大模型接口层，封装对话与 embedding 调用。

- `backend/channel/gewechat/gewe_channel.py`  
  微信登录、回调连接、消息解析、消息发送。

## 当前状态与后续计划

当前已完成：

- 微信接入与消息处理主链路
- 记忆检索增强（RAG）与角色化回复
- 计划调度与每日记忆总结基础能力

后续计划：

1. 完善长期记忆策略（分层记忆与更细粒度归档）
2. 优化前端交互体验与会话管理
3. 接入更多工具能力（如 MCP）
4. 扩展多模态输入能力（图像/语音等）