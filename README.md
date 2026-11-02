# 校园课程智能助手 · 业务脚手架

本仓库是 **FastAPI+Vue3通用业务脚手架**。

当前工程只提供 登录注册、用户管理、个人信息、文件上传等底座能力。

## 已包含能力

| 端 | 能力 |
| --- | --- |
| 前端 | 登录、注册、菜单主页、用户管理（管理员）、个人信息、修改密码 |
| 后端 | 登录注册、JWT、统一返回、全局异常、用户 CRUD、文件上传、静态资源挂载 |
| 数据库 | MySQL（推荐导入 `sql/backend.sql`，含表结构与演示账号） |

技术栈：Vue 3 + Element Plus + Axios · FastAPI + SQLAlchemy + JWT · MySQL。

## 环境要求

- Node.js：见 `frontend/package.json` 的 `engines`（建议 Node 22 LTS 或更高）
- Python 3.12+（与本地 `.venv` 保持一致即可）
- MySQL 8.0+

## 目录结构

```text
campus-course-agent/
├── sql/
│   └── backend.sql          # 用户表结构 + 演示账号
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/             # 路由
│   │   ├── services/        # 业务逻辑
│   │   ├── models/          # ORM
│   │   ├── schemas/         # 请求/响应模型
│   │   ├── common/          # 统一返回、异常
│   │   ├── dependencies/    # JWT 依赖
│   │   └── utils/
│   ├── uploads/             # 上传文件目录
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # 本地配置（勿提交真实密钥）
├── frontend/                # Vue3
│   ├── src/
│   │   ├── api/
│   │   ├── views/
│   │   ├── layouts/
│   │   └── utils/
│   └── .env.development
├── docs/
│   └── 课程大纲.md
└── README.md
```

## 1. 准备数据库

先在 MySQL 中创建空库（库名可自定，需与 `.env` 一致），例如：

```sql
CREATE DATABASE backend DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后导入仓库自带的初始化脚本（会建 `users` 表并写入演示账号）：

```powershell
mysql -u root -p backend < sql/backend.sql
```

也可用 Navicat、DBeaver、MySQL Workbench 等工具打开 `sql/backend.sql` 执行。

说明：

- 教学环境**优先导入** `sql/backend.sql`，这样开箱就有管理员和学生账号
- 后端启动时仍有 `Base.metadata.create_all`；若表已由 SQL 建好，不会覆盖已有数据
- `backend.sql` 含 `DROP TABLE IF EXISTS users`，重复执行会清空用户表，请勿在有正式数据的库上误跑

## 2. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

在 `backend` 目录创建或编辑 `.env`：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/backend
JWT_SECRET_KEY=请换成足够长的随机字符串
JWT_EXPIRE_HOURS=24
JWT_ALGORITHM=HS256
```

启动：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问：

- 健康检查：<http://127.0.0.1:8000/>
- 接口文档：<http://127.0.0.1:8000/docs>



VsCode Python相关的配置，搜索 打开  settings.json，设置文件保存格式化和自动导入：

```json
{
  "python.analysis.typeCheckingMode": "off",
  "redhat.telemetry.enabled": true,
  "python.analysis.autoImportCompletions": true,
  "python.languageServer": "Pylance",
  "python.analysis.extraPaths": ["./backend"],
  "editor.quickSuggestions": {
      "other": true,
      "comments": false,
      "strings": false
  },
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    },
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
}
```



## 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

开发地址一般为 <http://127.0.0.1:5173>。

`frontend/.env.development` 默认：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

开发模式下，Vite 已将 `/api`、`/uploads` 代理到 `127.0.0.1:8000`，一般无需改前端代理配置。



VsCode配置，搜索 打开  settings.json，设置文件保存格式化：

```json
{
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
 "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
}
```



## 4. 内置演示账号

导入 `sql/backend.sql` 后可用：

| 用户名 | 密码 | 角色 | 用途 |
| --- | --- | --- | --- |
| `admin` | `admin` | 管理员 | 登录后可见「用户管理」，可维护用户 |
| `aaa` | `123` | 学生 | 后续跨账号隔离、课表示例等演示 |
| `bbb`   | `123`   | 学生 | 同上，第二个学生账号 |

说明：

- 所有账号的密码已按当前 SQL 中的哈希校验通过，可直接登录
- 页面自行注册的用户角色固定为 `student`，不会自动成为管理员

## 5. 冒烟检查

按顺序确认：

1. 用 `admin` / `admin` 登录，侧栏出现「用户管理」
2. 查看用户列表，能看到 `admin`、`aaa`、`bbb`
3. 修改个人信息、上传头像
4. 修改密码后重新登录（演示完可改回，避免影响后续跟课）
5. 可选：再注册一个新账号，确认角色为普通学生

## 常见问题

| 现象 | 排查 |
| --- | --- |
| 后端启动报数据库连接错误 | 确认 MySQL 已启动、库已创建、`.env` 中 `DATABASE_URL` 账号密码正确 |
| 前端登录后接口 401 | 确认后端已启动；浏览器本地是否仍有过期 token，可清站点数据后重登 |
| 注册后没有「用户管理」 | 正常：新用户是 `student`；请用 `admin` 登录，或把该用户角色改为 `admin` |
| 导入 SQL 后登录失败 | 确认连的是导入过 `backend.sql` 的那个库；`admin` 密码为 `admin`；`aaa`/`bbb` 可先由管理员重置密码 |
| 上传头像失败 | 确认 `backend/uploads` 可写；文件类型在后端允许扩展名列表内 |
| 导入异常 / 应用起不来 | 先看启动终端完整报错；确认在 `backend` 目录、虚拟环境已激活，且依赖已按 `requirements.txt` 安装 |

## 说明

- 请勿把含真实密码的 `.env` 提交到公开仓库；对外分享时使用占位配置
- 本 README 描述的是**业务脚手架**的启动方式，不是完整 AI Agent 成品的使用说明
