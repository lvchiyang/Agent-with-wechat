# AI Agent项目

## 项目概述
本项目旨在构建一个基于大模型的AI Agent，支持多模型切换、角色管理和记忆管理等功能。项目还集成了RAG（Retrieval-Augmented Generation）和Agent Plan功能，以增强Agent的检索和规划能力。

## 项目结构
- `backend/`: 后端代码
  - `LLM/`: 大模型接口层
  - `Agent/`: Agent主进程
  - `Memory/`: 记忆管理模块
  - `config/`: 配置文件
- `frontend/`: 前端代码
  - `web.html`: 前端界面
- `README.md`: 项目说明文档
- `requirements.txt`: 依赖列表

## 项目功能
- **RAG（Retrieval-Augmented Generation）**：
  - 通过检索增强生成，结合外部知识库和上下文信息，提升Agent的回答质量和准确性。
  - 支持动态检索和实时更新知识库。

- **Plan功能**：
  - 提供任务规划和执行能力。

- **Agent 执行**：
  - 下一步要使用MCP，使Agent具有更强的能力。
  

## 快速开始

### 1. 配置 (默认即可)
```yaml
llm:
  active: ali_qwen # 选择使用的模型
  params:
    ali_qwen:
      api_key: "your_api_key"
```

### 2. 启动服务
```bash
cd backend
python Agent_hall.py
```

### 3. 访问前端
打开 `frontend/web.html`

## 依赖安装
在启动项目前，请确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

## 后续规划
1. 完善角色系统
2. MCP服务
3. 实现长期记忆
4. 支持多模态交互

## 贡献指南
欢迎贡献代码！请先阅读[贡献指南](CONTRIBUTING.md)。

## 许可证
本项目采用 [MIT 许可证](LICENSE)。