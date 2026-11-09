# 校园课程智能助手

一个面向课程管理与个人学习安排的 Web 项目。管理员维护课程、课表和课程资料；用户查看自己的课表、管理学习计划，并通过 AI 对话查询课表或检索已上传的课程资料。

## 功能

| 功能       | 说明                                                                          |
| ---------- | ----------------------------------------------------------------------------- |
| 账号与权限 | 注册、登录、个人信息、修改密码；管理员管理用户                                |
| 课程与课表 | 管理员维护课程和课表；普通用户仅查看自己的课表                                |
| 课程资料   | 管理员上传、预览、删除资料，并将文本写入向量库供检索                          |
| AI 对话    | 流式回答；通过 MCP 工具查询当前用户课表、检索课程资料、按明确请求保存学习计划 |
| 学习计划   | 用户查看、新建、删除自己的学习计划                                            |

技术栈：Vue 3、Vite、Element Plus、FastAPI、SQLAlchemy、MySQL、FastMCP、LangChain/LangGraph、Chroma。对话模型与向量模型使用 OpenAI 兼容接口，可在环境变量中配置服务地址和模型名。

## 项目结构

```text
backend/                 FastAPI 接口、MCP 服务、Agent 与业务代码
  app/api/               HTTP 路由
  app/services/          业务逻辑、Agent、资料检索
  mcp_server.py          独立的 MCP HTTP 服务
  .env.example           后端配置示例
  requirements.txt       Python 依赖
frontend/                Vue 3 前端
sql/backend.sql          用户表和演示账号初始化脚本
```

## 环境要求

- Node.js `^22.18.0` 或 `>=24.12.0`（见 `frontend/package.json`）
- Python 3.12+
- MySQL 8.0+
- Chroma HTTP 服务（默认监听 `127.0.0.1:8002`）
- 可用的对话模型和向量模型 API Key

以下命令以 Windows PowerShell 为例，从仓库根目录开始执行。后端、MCP、Chroma 和前端需要分别保持运行。

## 本地启动

### 1. 准备 MySQL

创建数据库，例如：

```sql
CREATE DATABASE backend DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

应用启动时使用 SQLAlchemy 的 `Base.metadata.create_all()` 创建当前模型对应的表。若需要演示账号，可以在**新建的演示数据库**中导入 `sql/backend.sql`。该脚本包含全部模型表和演示用户，并会删除同名表；不要对已有数据的数据库重复执行。已有数据库的结构变更需另行迁移，`create_all()` 不会修改已有列。可用 MySQL Workbench、DBeaver 等客户端导入该脚本。

### 2. 安装后端依赖并配置环境变量

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `backend/.env`，至少设置：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/backend
JWT_SECRET_KEY=请换成足够长的随机字符串
LLM_BASE_URL=https://你的对话模型兼容接口/v1
LLM_API_KEY=你的对话模型密钥
LLM_MODEL_NAME=你的模型名
EMBEDDING_BASE_URL=https://你的向量模型兼容接口/v1
EMBEDDING_API_KEY=你的向量模型密钥
EMBEDDING_MODEL=你的向量模型名
CHROMA_HOST=127.0.0.1
CHROMA_PORT=8002
```

其余选项及默认值见 `backend/.env.example` 和 `backend/app/config.py`。`JWT_SECRET_KEY` 的示例值也必须替换；不要提交真实的 `.env` 或密钥。

### 3. 启动 Chroma

在新终端从仓库根目录执行：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
chroma run --path ./data/kb/chroma --host 127.0.0.1 --port 8002
```

地址需与 `CHROMA_HOST`、`CHROMA_PORT` 一致。课程资料的入库和检索依赖该服务；MySQL 保存资料记录，向量片段保存在 Chroma。上述数据目录位于已忽略的 `backend/data/kb/` 内。

### 4. 启动后端与 MCP

在两个终端分别执行（均从仓库根目录开始）：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python mcp_server.py
```

FastAPI 默认位于 `http://127.0.0.1:8000`，接口文档位于 `http://127.0.0.1:8000/docs`；MCP 默认位于 `http://127.0.0.1:8001/mcp`。修改 MCP 服务代码后，需要重启对应的 `python mcp_server.py` 进程。

### 5. 启动前端

在新终端从仓库根目录执行：

```powershell
cd frontend
npm install
npm run dev
```

打开 Vite 输出的地址（通常是 `http://localhost:5173`）。前端开发配置默认请求 `http://127.0.0.1:8000`；如需调整，修改 `frontend/.env.development` 中的 `VITE_API_BASE_URL`。Vite 还将 `/api` 和 `/uploads` 代理到后端。
