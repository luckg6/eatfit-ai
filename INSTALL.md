# 📦 INSTALL.md — EatFit AI 一键安装手册

> 这份文档是为 **Claude Code / Codex / Cursor 之类的 Agent 编排执行**而写的。每一步都带：
> - **🎯 目标** — 这一步要达成什么
> - **▶ 命令** — 在哪个目录下、用什么 shell 执行什么命令
> - **✅ 验证** — 怎么确认这步真的成了（CC 可以用这个判断要不要重试 / 报错）
>
> 全程 **不需要交互输入**；所有需要填的密钥都在最后一步 `.env` 里。建议 CC 顺序执行 0 → 8 一次性跑完。
>
> **平台说明**：仓库在 Windows + Git Bash 上开发，命令均以 Bash 语法给出；macOS/Linux 直接照跑，Windows 用 Git Bash 或 WSL。

---

## 🧰 0. 环境前置要求

执行前，必须先在宿主机就绪以下基础组件。CC 可以用每行末尾的"验证"命令逐一探测，缺啥装啥。

| 组件 | 最低版本 | 验证命令 | 缺失时怎么装 |
|------|---------|---------|------------|
| Git | 2.30+ | `git --version` | https://git-scm.com/downloads |
| Python | **3.11+** | `python --version` | https://www.python.org/downloads/ |
| pip | 23+ | `pip --version` | 随 Python |
| Node.js | **18+** | `node --version` | https://nodejs.org/ |
| npm | 9+ | `npm --version` | 随 Node |
| PostgreSQL | **17** | `psql --version` | https://www.postgresql.org/download/ 或本文 §1-B Docker |
| Ollama | latest | `ollama --version` | https://ollama.com/download |
| mkcert *(可选)* | latest | `mkcert -version` | https://github.com/FiloSottile/mkcert（不装也能用 openssl 兜底）|
| OpenSSL *(可选)* | 1.1+ | `openssl version` | 通常随 git / 系统自带 |

> ⚠️ 如果 CC 在 Windows + Git Bash 下跑，注意 PowerShell 内置的 `psql.exe` 路径可能没在 PATH，建议把 `C:\Program Files\PostgreSQL\17\bin` 加进 PATH，或用绝对路径调用。

---

## 📥 1. 准备 PostgreSQL 17 + pgvector

### 方式 A — 本地 PG（推荐，调试方便）

```bash
# macOS（brew）
brew install postgresql@17
brew services start postgresql@17

# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y postgresql-17 postgresql-17-pgvector
sudo systemctl start postgresql

# Windows：用官方 EDB 安装包装好后，确保服务已在运行
```

### 方式 B — Docker（一行起容器，自带 pgvector）

```bash
docker run -d --name eatfit-pg \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=eatfit_ai \
  -p 5432:5432 \
  pgvector/pgvector:pg17
```

### ✅ 验证

```bash
# 任一方式都用这条验证连通
PGPASSWORD=root psql -U postgres -h localhost -d postgres -c "SELECT version();"
```

预期输出：`PostgreSQL 17.x ...`。

---

## 🗄️ 2. 创建库 + 启用 pgvector 扩展

```bash
# 1) 建库（本地装时；Docker 方式已经在启动参数里建好了，本步可跳过）
PGPASSWORD=root psql -U postgres -h localhost -d postgres -c "CREATE DATABASE eatfit_ai;"

# 2) 启用 vector 扩展
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### ✅ 验证

```bash
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -c "\dx vector"
```

预期：列出 `vector | 0.8.x | public | vector data type and ...` 一行。

---

## 🏗️ 3. 初始化 schema —— **一条命令搞定 10 张表**

`backend/sql/pg/init_pg.sql` 是**唯一**需要执行的 SQL —— 旧 MySQL 时代的 `001-003` 已并入，`004_harden_memory_items.sql` 的 CHECK 约束 / `memory_items_touch_updated_at` 触发器 / `idx_memory_user_status_last_used` / `idx_memory_embedding_pending` / `idx_memory_source_message` 索引也都固化在了建表语句里。脚本是 **idempotent** 的，重复执行不会报错。

```bash
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -f backend/sql/pg/init_pg.sql
```

### ✅ 验证

```bash
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -c "\dt"
```

预期：**正好 10 张表**：

```
users  user_food_profiles  memory_items  meal_logs
advice_sessions  chat_messages  weight_records  body_fat_records
training_records  diet_advice_records
```

继续验证 `memory_items` 上的向量列 + 触发器：

```bash
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -c "
  SELECT column_name, udt_name FROM information_schema.columns
  WHERE table_name='memory_items' AND column_name IN ('embedding','embedding_status');"
```

预期 `embedding | vector` 和 `embedding_status | varchar`。

---

## 🧠 4. 启动 Ollama 并拉取嵌入模型（1024 维）

```bash
# 启动 ollama 后台进程（macOS/Linux 在新 terminal 跑这条；Windows 桌面版安装后会自动起服务）
ollama serve &

# 拉模型（约 ~600MB）
ollama pull qwen3-embedding:0.6b
```

### ✅ 验证

```bash
# 1) 服务在
curl -s http://localhost:11434/api/tags | grep -q "qwen3-embedding" && echo "OK"

# 2) 真的能 embed
curl -s http://localhost:11434/api/embeddings \
  -d '{"model":"qwen3-embedding:0.6b","prompt":"hello"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print('dim =', len(d['embedding']))"
```

预期：`OK` 和 `dim = 1024`。

---

## ⚙️ 5. 后端：装依赖

```bash
cd backend

# venv 隔离（强烈建议）
python -m venv .venv

# 激活
source .venv/bin/activate            # macOS / Linux
source .venv/Scripts/activate        # Windows Git Bash

# 装包
pip install -U pip
pip install -r requirements.txt
```

`requirements.txt` 锁的版本一览（13 个包）：

```
fastapi==0.109.2              # Web 框架
uvicorn[standard]==0.27.1     # ASGI server
sqlalchemy==2.0.25            # ORM
pymysql==1.1.0                # 仅迁移脚本用到（migrate_mysql_to_pg.py），新部署不会触发
cryptography==42.0.2          # pymysql 依赖
pydantic==2.6.1               # 数据校验
pydantic-settings==2.1.0      # .env 读取
python-jose[cryptography]==3.3.0   # JWT
passlib[bcrypt]==1.7.4        # 密码哈希
python-dotenv==1.0.1          # .env 兜底
httpx==0.26.0                 # LLM HTTP 客户端 + Ollama embedding 调用
mcp==1.0.0                    # 百度地图 MCP client
psycopg[binary]==3.2.3        # PG + pgvector 驱动
```

### ✅ 验证

```bash
python -c "import fastapi, sqlalchemy, psycopg, httpx, mcp, jose, passlib; print('all imports ok')"
```

预期：`all imports ok`。

---

## 🔐 6. 后端：写 `.env`

```bash
cd backend
cp .env.example .env
```

然后**逐项确认 / 修改**以下值（这是 `app/core/config.py` 的 `Settings` 类全集）：

```env
# ----- 数据库 -----
# 如果你 §1 用的不是 postgres/root，改这里
DATABASE_URL=postgresql+psycopg://postgres:root@localhost:5432/eatfit_ai

# ----- JWT（生产请改 SECRET）-----
JWT_SECRET_KEY=please-change-this-secret-key-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# ----- LLM（OpenAI 兼容协议）-----
# 留空 LLM_API_KEY 系统会自动切到 MockLLMService（无外网也能跑通对话流）
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# ----- 本地 Ollama embedding（§4 已就绪）-----
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIM=1024
# 混合排序权重: score = vw*(1-cos_dist) + iw*(importance/10)
MEMORY_VECTOR_WEIGHT=0.6
MEMORY_IMPORTANCE_WEIGHT=0.4

# ----- 百度地图（可选；不填则餐厅搜索走 mock）-----
BAIDU_MAP_AK=

# ----- CORS（vite 默认 HTTPS，所以是 https）-----
FRONTEND_ORIGIN=https://localhost:5173
```

### ✅ 验证

```bash
cd backend
python -c "from app.core.config import settings; print('DB:', settings.DATABASE_URL); print('CORS:', settings.FRONTEND_ORIGIN); print('EMBED:', settings.EMBEDDING_MODEL)"
```

预期能正确打印出三行。

---

## 🎨 7. 前端：装依赖 + 生成 HTTPS 自签证书

`frontend/vite.config.ts` 强制启用 HTTPS（`server.https` 指向 `./key.pem` 和 `./cert.pem`），目的是让 `navigator.geolocation` 在所有设备上都能拿到 GPS。**没证书 vite 启动会直接报 `ENOENT: cert.pem`**。

```bash
cd frontend

# 1) 装依赖
npm install

# 2) 生成自签证书（任选其一）
# 推荐：mkcert（系统信任，没浏览器警告）
mkcert -install
mkcert -key-file key.pem -cert-file cert.pem localhost 127.0.0.1 ::1

# 兜底：openssl（会有"不安全"警告，点继续访问即可）
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 365 -subj "/CN=localhost"
```

前端依赖清单（来自 `frontend/package.json`）：

| 类型 | 包 |
|------|---|
| dependencies | `react@^18.2`, `react-dom@^18.2`, `react-router-dom@^6.22`, `axios@^1.6.7`, `dayjs@^1.11.10` |
| devDependencies | `vite@^5.1`, `@vitejs/plugin-react@^4.2`, `typescript@^5.3`, `tailwindcss@^3.4`, `postcss@^8.4`, `autoprefixer@^10.4`, `@types/react@^18.2`, `@types/react-dom@^18.2` |

### ✅ 验证

```bash
cd frontend
ls -l key.pem cert.pem      # 两个文件都在
ls node_modules/.package-lock.json   # 依赖装好了
```

---

## 🚀 8. 启动 & 冒烟测试

开**两个**终端，分别启后端、前端。

### 终端 A — 后端

```bash
cd backend
source .venv/bin/activate        # 或 .venv/Scripts/activate
uvicorn app.main:app --reload --port 8000
```

启动日志应出现：

```
EatFit AI API starting up...
Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

如果日志里出现 `Cannot connect to database` —— 回到 §1 / §2 修复。

### 终端 B — 前端

```bash
cd frontend
npm run dev
```

启动日志应出现：

```
VITE v5.x  ready in xxx ms
➜  Local:   https://localhost:5173/
```

### ✅ 端到端冒烟

```bash
# 1) 后端健康检查
curl -s http://localhost:8000/api/health
# 预期：{"status":"ok",...} 或类似 JSON

# 2) OpenAPI 文档可访问
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs
# 预期：200

# 3) 浏览器打开
#   https://localhost:5173    （注意是 https，自签证书首次有警告）
```

注册一个账号 → 进对话页 → 随便说一句"我中午吃了一个汉堡" → 能看到 `agent_step` 流式 trace + `meal_log` 确认卡弹出，整条链路就跑通了。

---

## 🆘 常见错误速查

| 现象 | 原因 | 修复 |
|------|------|------|
| `psql: FATAL: password authentication failed` | PG 密码不是 `root` | 改 `.env` 里 `DATABASE_URL` 的密码；或重置 PG 密码 |
| `ERROR: extension "vector" is not available` | pgvector 没装 | 本地 PG 装 `pgvector` 包；或换 §1-B Docker 方式 |
| 后端启动报 `Cannot connect to database` | §1/§2 没就绪 / `.env` DATABASE_URL 错 | 用 §2 的 `\dx vector` 命令逐项排查 |
| 前端 `Error: ENOENT: ... cert.pem` | §7 的证书没生成 | 重做 §7 的 mkcert / openssl 步骤 |
| 前端打开浏览器 CORS 报错 | `.env` 里 `FRONTEND_ORIGIN` 还是 http | 改成 `https://localhost:5173`，**重启 uvicorn**（uvicorn 不会热加载 `.env`） |
| `httpx.ConnectError: ... 11434` | Ollama 没起 | `ollama serve &` 再重试，或检查 `OLLAMA_BASE_URL` |
| 对话回的内容全是 mock 模板 | `LLM_API_KEY` 留空了 | 这是预期行为；要真 LLM 就填 `.env` 里 `LLM_API_KEY` |
| `1024` 维 embedding 写不进去（NULL） | Ollama 不可用 / 模型未拉 | 跑 §4 的两条 curl 验证，再跑 `cd backend && PYTHONPATH=. python sql/pg/backfill_embeddings.py` 回填 |
| Windows 下 `source .venv/bin/activate` 报错 | Windows 路径不一样 | 用 `source .venv/Scripts/activate`（Git Bash） |

---

## 🔁 重装 / 重置数据库

如果想完全重来一次：

```bash
# 1) 删库重建
PGPASSWORD=root psql -U postgres -h localhost -d postgres -c "DROP DATABASE IF EXISTS eatfit_ai;"
PGPASSWORD=root psql -U postgres -h localhost -d postgres -c "CREATE DATABASE eatfit_ai;"
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -f backend/sql/pg/init_pg.sql

# 2) 清 venv / node_modules
rm -rf backend/.venv frontend/node_modules

# 3) 回到 §5 重做
```

---

## 📎 关键文件索引（供 CC 快速跳转）

| 路径 | 作用 |
|------|------|
| `backend/sql/pg/init_pg.sql` | **唯一**的 PG 建表脚本（idempotent） |
| `backend/sql/pg/migrate_mysql_to_pg.py` | 老 MySQL 数据 → PG 的迁移工具（新部署用不到） |
| `backend/sql/pg/backfill_embeddings.py` | 给 `memory_items` 回填 1024 维向量的 CLI |
| `backend/.env.example` | `.env` 模板 |
| `backend/app/core/config.py` | `Settings` 全部环境变量定义 |
| `backend/app/main.py` | FastAPI 入口（含 CORS、`/api` 路由挂载） |
| `backend/requirements.txt` | 锁版本的 Python 依赖 |
| `frontend/vite.config.ts` | HTTPS / proxy `/api` 配置 |
| `frontend/package.json` | npm 脚本 + 前端依赖 |
| `README.md` | 完整技术栈、API、Agent 架构说明 |
