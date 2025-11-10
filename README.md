## 智面工坊 · Interview Forge

一个以学习-面试-补学闭环为核心的智能面试系统。通过个性化任务树、AI 面试与动态补学机制，帮助候选人精准查漏补缺、稳步升级“面试战力”。

- **闭环学习**：任务 → 面试 → 弱点识别 → 补学任务
- **岗位定制**：按岗位生成专属任务树
- **Agentic RAG**：知识库检索增强生成
- **训练支持**：SFT / RLHF / Benchmark 评估

---

## 环境与要求

- **操作系统**：Windows 10/11（兼容 macOS / Linux）
- **Python**：3.9+（推荐 3.10/3.11）
- **Node.js**：18+（含 npm）
- **MySQL**：8.0+
- **PowerShell**：用于执行命令

项目结构（节选）：
- `backend/`：FastAPI 后端
- `frontend/`：React + Vite 前端
- `database/`：MySQL 初始化脚本
- `Mysql文件导入/`：可选数据导入脚本合集

---

## 0. 解压与进入项目

将压缩包解压至你选择的目录（如 `D:\PycharmProjects（D盘）\smart-interview-platform`），并在 PowerShell 进入项目根目录：

```powershell
cd "D:\PycharmProjects（D盘）\smart-interview-platform"
```

---

## 1. 初始化数据库（MySQL 8.0）

1) 登录 MySQL（以 root 为例）：
```powershell
mysql -u root -p
```

2) 执行初始化脚本（创建数据库与核心表）：
```sql
source database/init.sql;
```

3) 可选：导入更丰富的示例数据（中文目录名不影响执行）：
```sql
-- 视需要选择导入，以下为示例
source Mysql文件导入/smart_interview_users.sql;
source Mysql文件导入/smart_interview_tasks.sql;
source Mysql文件导入/smart_interview_interviews.sql;
source Mysql文件导入/smart_interview_knowledge_base.sql;
```

4) 验证：
```sql
USE smart_interview;
SHOW TABLES;
```

数据库默认名：`smart_interview`（见 `database/init.sql`）

---

## 2. 后端环境（FastAPI）

1) 创建并激活虚拟环境：
```powershell
python -m venv venv
.\venv\Scripts\activate
```

2) 安装依赖：
```powershell
cd backend
pip install -r requirements.txt
```

3) 配置环境变量（强烈建议使用 `.env`，不要提交到版本库）  
在 `backend` 目录下创建 `.env`：

```env
# MySQL 连接
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的数据库密码
DB_NAME=smart_interview

# Qwen / DashScope
QWEN_API_KEY=你的Qwen密钥
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# JWT
SECRET_KEY=请替换为随机复杂字符串
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 前端地址（CORS）
FRONTEND_URL=http://localhost:3000
```

说明：
- 后端配置由 `backend/app/config.py` 读取 `.env`。
- 源码中的默认密钥仅为占位，请一定改为自己的密钥。

4) 启动后端（默认 8000 端口）：
```powershell
# 方式一：模块运行（推荐）
python -m app.main

# 或方式二：Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

健康检查：
- `http://localhost:8000/api/health` → `{"status":"healthy"}`

---

## 3. 前端环境（React + Vite）

1) 安装依赖：
```powershell
cd ../frontend
npm install
```

2) 启动前端（默认 3000 端口）：
```powershell
npm run dev
```

前端开发代理已在 `frontend/vite.config.js` 配置：
- 将以 `/api` 开头的请求代理到 `http://localhost:8000`

---

## 4. 访问与联调

- 前端入口：`http://localhost:3000`
- 后端接口：`http://localhost:8000`
- 主要路由（节选）：
  - 认证：`/api/auth/*`
  - 任务：`/api/tasks/*`
  - 面试：`/api/interviews/*`
  - 健康：`/api/health`

---

## 5. 常见问题排查

- **数据库连接失败**
  - 确认 MySQL 已启动，账户/密码正确
  - 数据库 `smart_interview` 存在（可用 `init.sql` 重建）
  - `.env` 与 `backend/app/config.py` 配置一致

- **前端无法调用后端**
  - 确认后端已在 8000 端口运行
  - 确认前端在 3000 端口，`vite.config.js` 代理已生效
  - 检查浏览器控制台与终端代理日志

- **Qwen 调用失败**
  - 检查 `QWEN_API_KEY` 是否有效、余额是否充足
  - 网络与 `QWEN_API_BASE` 可达

- **训练运行较慢或失败**
  - 无 GPU 时训练速度较慢属正常
  - 检查训练数据格式与路径（`./data/training`）

---

## 6. 进阶：训练与数据

- SFT / RLHF / Benchmark 入口：
  - `backend/app/training/sft_trainer.py`
  - `backend/app/training/rlhf_trainer.py`
  - `backend/app/training/benchmark.py`
- 知识库与训练数据目录建议：
  - `data/knowledge_base/`
  - `data/training/`

---

## 7. 项目结构（简版）
smart-interview-platform/
├─ backend/ # FastAPI 后端
│ ├─ app/
│ │ ├─ api/ # 路由（auth、tasks、interviews、chat、resume 等）
│ │ ├─ models/ # SQLAlchemy 模型
│ │ ├─ services/ # 业务服务（RAG、LLM、个性化等）
│ │ ├─ database/ # 连接与会话
│ │ ├─ config.py # 配置（.env）
│ │ └─ main.py # 应用入口
│ ├─ requirements.txt
│ └─ training/ # SFT / RLHF / Benchmark
├─ frontend/ # React + Vite 前端
│ ├─ src/
│ └─ vite.config.js
├─ database/
│ └─ init.sql # 数据库初始化
└─ Mysql文件导入/ # 可选数据导入

---

## 8. 许可证与贡献

- **许可证**：MIT
- **贡献**：欢迎提交 Issue / PR，或在 `database/` 中补充更丰富的数据脚本
