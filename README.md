# AI女友项目

## 项目架构

### 1. 后端架构
- **大模型接口层**：将云端大模型功能解耦，支持多个模型切换
  - 位置：backend/bot/下的不同文件夹
  - 统一LLM API接口供Agent调用
  - 当前支持：阿里通义千问，可扩展其他模型

- **Agent主进程**：backend/Agent
  - 监听9001端口
  - 处理前端WebSocket连接
  - 调用LLM并返回结果
  - 集成角色管理、情感分析、记忆管理等模块

- **核心模块**
  - 角色管理：管理AI女友人设 (backend/character)
  - 情感分析：分析用户情绪 (backend/modules/emotion_analyzer.py)
  - 记忆管理：维护对话历史 (backend/modules/memory_manager.py)

### 2. 前端架构
- 简单的对话界面
- WebSocket实时通信
- 位置：frontend/index.html

## 快速开始

### 1. 配置
编辑 backend/config/settings.yaml:
yaml
llm:
active: ali_qwen # 选择使用的模型
params:
ali_qwen:
api_key: "your_api_key"


### 2. 启动服务
bash
cd backend
python main.py


### 3. 访问前端
打开 frontend/index.html

## 后续规划
1. 完善角色系统
2. 添加情感分析
3. 实现长期记忆
4. 支持多模态交互

## 项目结构
Agent-with-wechat/
├── backend/ # 后端代码
│ ├── Agent/ # Agent主程序
│ ├── config/ # 配置文件
│ ├── character/ # 角色设定
├── frontend/ # 前端代码
└── requirements.txt # 依赖列表

## 依赖安装

在启动项目前，请确保已安装所有依赖：