# 🍱 EatFit AI - 外食健康饮食助手

EatFit AI 是一个面向学生、上班族、健身人群的**外食健康饮食 Agent**。当你经常点外卖、吃食堂、在外就餐却想减脂 / 增肌 / 控糖 / 改善睡眠时，它用对话 + 长期记忆 + 餐厅地图工具，帮你把"吃什么、怎么点"做对。

后端基于 **FastAPI + PostgreSQL 17 + pgvector**，前端基于 **React 18 + TypeScript**，长期记忆使用本地 **Ollama (`qwen3-embedding:0.6b`)** 生成 1024 维向量并做混合检索；餐厅推荐接入**百度地图 MCP**。

---

## ✨ 功能列表

### 💬 核心功能
- **对话式饮食助手** — 自然语言交互，ReAct 架构的 AI Agent
- **多意图并行识别** — 规则 + LLM 的 `classify_multi`；一次对话可同时识别"记录饮食 + 提取记忆 + 资料更新"
- **饮食记录** — 自动估算热量与三大宏量营养素；6 类餐次（早/午/晚/加餐/训练后/夜宵）+ 8 类场景（食堂/外卖/便利店/快餐/餐厅/自己做/聚餐/其他）
- **用户画像管理** — 身高、体重、目标、预算、训练频率、饮食偏好、过敏、睡眠敏感等
- **长期记忆系统（pgvector）** — 12 种记忆类型（饮食偏好、不喜欢、过敏、目标、预算、地点、场景、睡眠、身体反应、限制、习惯、其他）；高重要性需用户确认，低风险自动保存
- **会话历史管理** — 多会话、上下文连续、`scenario` + `is_training_day` 标识
- **SSE 流式响应** — 实时显示 Agent 推理过程：`intent_detected` / `agent_step` / `action_pending` / `memory_pending` / `message_done` 等事件
- **GPS 位置感知** — 前端 `navigator.geolocation` 拿到经纬度，传给 Agent；无 GPS 时回退到 IP 定位
- **Pending Action 确认卡** — 饮食记录 / 资料更新 / 记忆抽取先挂起，用户在前端确认卡里点确认才落库
- **Weekly Review** — 每周饮食复盘（基于训练、体重、体脂、饮食记录）
- **Mock 模式** — 无 `LLM_API_KEY` 时自动启用 `MockLLMService`，返回示例数据

### 🛠️ Agent 工具层
- `ProfileTools` — 用户画像读取 / 更新
- `MemoryTools` — 记忆 CRUD、混合排序（向量 + 重要性）、自动嵌入、批量回填
- `MealTools` — 饮食记录解析 / 营养估算 / 今日 / 范围汇总
- `ChatTools` — 会话消息管理、pending action 收集
- `RestaurantTools` — 附近餐厅搜索 + 详情查询（百度地图 MCP 集成）
- `MCP Client` — 百度地图地理编码 / 地点搜索 / 详情 MCP 工具调用
- `EmbeddingService` — Ollama `qwen3-embedding:0.6b` 异步 / 同步调用 + pgvector 字面量格式化

### 🗺️ 地图集成（百度地图 MCP）
- 地址地理编码（`map_geocode`）
- 地点关键词搜索（`map_search_places`）
- 地点详情查询（`map_place_details`）
- IP 定位（`map_ip_location`，含 BD-09MC → BD-09LL 坐标转换）

---

## 💻 技术栈

### 🐍 后端
| 组件 | 版本 / 说明 |
|------|------|
| Python | 3.11+ |
| Web 框架 | FastAPI 0.109.2 + Uvicorn 0.27.1 |
| ORM | SQLAlchemy 2.0.25 |
| 数据校验 | Pydantic 2.6.1 + pydantic-settings 2.1.0 |
| 数据库 | **PostgreSQL 17 + pgvector**（`vector(1024)` 列） |
| 向量嵌入 | **Ollama + `qwen3-embedding:0.6b`**（本地 1024 维） |
| 数据库驱动 | `psycopg[binary]` 3.2.3 |
| LLM 客户端 | OpenAI-compatible HTTP（`httpx` 0.26.0） |
| MCP | `mcp` 1.0.0（百度地图 HTTP MCP 端点） |
| Auth | `python-jose[cryptography]`（JWT HS256）+ `passlib[bcrypt]` |
| 迁移 | `pymysql` 1.1.0 + `cryptography` 42.0.2（旧 MySQL 兼容） |
| 配置 | `python-dotenv` 1.0.1 |

### ⚛️ 前端
| 组件 | 版本 / 说明 |
|------|------|
| 框架 | React 18.2 + React DOM 18.2 |
| 语言 | TypeScript 5.3 |
| 构建 | Vite 5.1 + `@vitejs/plugin-react` 4.2 |
| 路由 | React Router DOM 6.22 |
| 样式 | Tailwind CSS 3.4 + PostCSS + Autoprefixer |
| HTTP | Axios 1.6.7（带请求 / 响应拦截器） |
| 时间 | dayjs 1.11.10 |

---

## 📁 项目目录

```
eatfit-ai/
├── backend/
│   ├── app/
│   │   ├── api/              # REST 路由
│   │   │   ├── auth.py           # /api/auth (register/login/me/logout)
│   │   │   ├── profile.py        # /api/profile
│   │   │   ├── meals.py          # /api/meals (CRUD + summary)
│   │   │   ├── memories.py       # /api/memories
│   │   │   ├── advice.py         # /api/advice (sessions + SSE stream)
│   │   │   ├── records.py        # /api/weights, /api/body-fat, /api/trainings
│   │   │   ├── users.py          # /api/users/auto-memory
│   │   │   └── health.py         # /api/health
│   │   ├── core/             # config, security
│   │   ├── db/               # database.py (PG + pgvector)
│   │   ├── models/           # SQLAlchemy 模型（users/food_profile/memory/meal_log/advice/chat_message/records）
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # llm_service / advice_service / memory_extractor / embedding_service
│   │   ├── agent/            # diet_agent_loop (ReAct) / intent_classifier (+_llm)
│   │   ├── prompts/          # diet_advice / memory_extractor / daily_plan / weekly_review
│   │   ├── tools/            # profile/memory/meal/chat/restaurant tools, mcp_client
│   │   └── main.py           # FastAPI 入口
│   ├── sql/
│   │   ├── init.sql          # 旧 MySQL 建表（仅作参考，新部署用不到）
│   │   ├── migrations/       # 旧 MySQL 增量迁移
│   │   │   ├── 001_add_chat_messages.sql
│   │   │   ├── 002_enhance_memory_and_meal_tables.sql
│   │   │   ├── 003_add_restaurant_context.sql
│   │   │   ├── 004_harden_memory_items.sql   # CHECK + 触发器 + 索引，已并入 init_pg.sql
│   │   │   ├── 005_drop_restaurant_context.sql  # 删除 dead-state 字段，餐厅数据走 chat_messages.action_data
│   │   │   └── 006_drop_user_question.sql       # 删除冗余字段（与 title 内容重复，前端只读 title）
│   │   └── pg/               # 新 PG 体系
│   │       ├── init_pg.sql                    # PG + pgvector 建表（vector(1024)，含 004 全部硬化项）
│   │       ├── migrate_mysql_to_pg.py         # MySQL -> PG 全量迁移
│   │       └── backfill_embeddings.py         # 批量回填 embedding
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/              # API 封装（auth/profile/meals/memories/advice/weights/bodyFat/trainings/user）
│   │   ├── components/chat/  # 聊天组件（见下）
│   │   ├── pages/            # 10 个页面
│   │   ├── types/            # TypeScript 类型
│   │   ├── utils/            # AuthContext / ThemeContext / foodDetection
│   │   ├── App.tsx           # 路由配置（BrowserRouter + AuthProvider + ThemeProvider）
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── docs/
└── README.md
```

#### 🎨 聊天组件清单（`frontend/src/components/chat/`）
- `ChatMessageList` — 消息列表 + 确认卡渲染
- `ChatInput` — 自动撑高的 textarea 输入框
- `ChatContextBar` — 场景（食堂/外卖/便利店/快餐/餐厅/聚餐/其他）+ 训练日开关
- `AgentTracePanel` — Agent 步骤 trace 面板（多 step 中文化）
- `MealLogConfirmCard` — 饮食记录确认卡
- `ProfileUpdateConfirmCard` — 资料更新确认卡
- `MemoryConfirmCard` — 记忆确认卡（含 12 种类型映射）
- `RestaurantConfirmCard` — 附近餐厅选择卡

---

## 🚀 快速启动

### 1️⃣ 启动 PostgreSQL 17 并启用 pgvector

#### 方式 A：本地 PG（推荐，便于跑通向量查询）
```bash
# macOS / Linux (brew)
brew install postgresql@17
brew services start postgresql@17

# 创建库
createdb -U postgres eatfit_ai
psql -U postgres -d eatfit_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 方式 B：docker compose
```bash
# 启动一个 pgvector 容器（仓库自带的 docker-compose.yml 只含旧 MySQL，可按需扩展）
docker run -d --name eatfit-pg \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=eatfit_ai \
  -p 5432:5432 \
  pgvector/pgvector:pg17

docker exec eatfit-pg psql -U postgres -d eatfit_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2️⃣ 初始化数据库表结构

新装只需要执行 `init_pg.sql` 这一个文件就够了 —— 它已经把 `001-003` 的旧迁移和 `004_harden_memory_items.sql` 的全部 CHECK 约束 / `memory_items_touch_updated_at` 触发器 / `idx_memory_user_status_last_used` `idx_memory_embedding_pending` `idx_memory_source_message` 等索引固化进了建表语句。

```bash
# 0) 确保 vector 扩展已启用（用本地 PG 时是这一行；用 pgvector/pgvector 镜像可跳过）
psql -U postgres -h localhost -d eatfit_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 1) 建全部表 + 约束 + 触发器 + 索引（idempotent，可重复跑）
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -f backend/sql/pg/init_pg.sql
```

执行完后会得到 10 张表：`users` / `user_food_profiles` / `memory_items`（含 `vector(1024)`）/ `meal_logs` / `advice_sessions` / `chat_messages` / `weight_records` / `body_fat_records` / `training_records` / `diet_advice_records`。

> 如果是从旧 MySQL 迁过来的：**先**在 PG 上跑 `init_pg.sql`，**再**用 `backend/sql/pg/migrate_mysql_to_pg.py` 把数据搬过来，最后跑 `backfill_embeddings.py` 回填向量。详见 [🔄 数据迁移（MySQL → PostgreSQL）](#-数据迁移mysql--postgresql)。

### 3️⃣ 启动本地 Ollama 并拉取 embedding 模型

```bash
# 安装 ollama（https://ollama.com/download）
ollama serve
ollama pull qwen3-embedding:0.6b
```

### 4️⃣ 配置后端环境变量

```bash
cd backend
cp .env.example .env
```

`.env` 关键项：

```env
# PostgreSQL + pgvector
DATABASE_URL=postgresql+psycopg://postgres:root@localhost:5432/eatfit_ai

# JWT
JWT_SECRET_KEY=please-change-this-secret-key-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# LLM (OpenAI-compatible)
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# 本地 Ollama embedding
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIM=1024
# 混合排序权重：score = vw*(1-cos_dist) + iw*(importance/10)
MEMORY_VECTOR_WEIGHT=0.6
MEMORY_IMPORTANCE_WEIGHT=0.4

# 百度地图（可选，用于餐厅搜索）
BAIDU_MAP_AK=your-baidu-map-api-key

# CORS（前端跑在 HTTPS 时要改成 https，否则浏览器拒绝跨域）
FRONTEND_ORIGIN=https://localhost:5173
```

> `app/main.py` 里 CORS 默认还兜底放行了 `http://localhost:5173` 和 `http://localhost:3000`，但既然 `vite` 默认走 HTTPS，配 `https://localhost:5173` 是最安全的姿势。

### 5️⃣ 安装依赖并启动后端

后端需要 Python 3.11+。建议先建一个 venv，避免污染全局环境。

```bash
cd backend
python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows (Git Bash) — 仓库目前在 Win 上开发
source .venv/Scripts/activate

pip install -r requirements.txt
```

`requirements.txt` 实际锁的版本（与 README 顶部技术栈表一一对应）：

```
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
pymysql==1.1.0              # 仅用于跑 migrate_mysql_to_pg.py，新部署用不到
cryptography==42.0.2
pydantic==2.6.1
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
httpx==0.26.0               # LLM HTTP / Ollama embedding 都靠它
mcp==1.0.0                  # 百度地图 MCP client
psycopg[binary]==3.2.3      # PG + pgvector 驱动
```

启动：

```bash
uvicorn app.main:app --reload --port 8000
```

后端运行在 <http://localhost:8000>，OpenAPI 文档在 <http://localhost:8000/docs>。

### 6️⃣ 启动前端

```bash
cd frontend
npm install
npm run dev
```

> ⚠️ `vite.config.ts` 强制启用 HTTPS（`server.https` 指向 `./key.pem` 和 `./cert.pem`），主要是为了让浏览器的 `navigator.geolocation` 在非 localhost 设备上也能拿到 GPS。**第一次跑前必须在 `frontend/` 下放好自签证书**，否则 `vite` 启动会报 `ENOENT: cert.pem`。
>
> 用 `mkcert` 一键生成（推荐）：
> ```bash
> cd frontend
> mkcert -install
> mkcert -key-file key.pem -cert-file cert.pem localhost 127.0.0.1 ::1
> ```
>
> 或者用 OpenSSL：
> ```bash
> cd frontend
> openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 365 -subj "/CN=localhost"
> ```
>
> 启动成功后访问 **<https://localhost:5173>**（注意是 `https`），首次会有自签证书警告，点"继续访问"。`/api` 已通过 vite 代理转发到 `http://localhost:8000`，前端代码里直接写相对路径即可。

前端依赖（来自 `frontend/package.json`）：

| 依赖类型 | 包 |
|---------|---|
| dependencies | `react@^18.2`, `react-dom@^18.2`, `react-router-dom@^6.22`, `axios@^1.6.7`, `dayjs@^1.11.10` |
| devDependencies | `vite@^5.1`, `@vitejs/plugin-react@^4.2`, `typescript@^5.3`, `tailwindcss@^3.4`, `postcss@^8.4`, `autoprefixer@^10.4`, `@types/react@^18.2`, `@types/react-dom@^18.2` |

`package.json` 提供 3 个脚本：`dev`（vite 开发服务器）/ `build`（`tsc && vite build`）/ `preview`（构建产物预览）。

### 7️⃣（可选）回填历史记忆的向量

```bash
cd backend
PYTHONPATH=. python sql/pg/backfill_embeddings.py
```

脚本会扫描 `embedding IS NULL OR embedding_status != 'ready'` 的行，调用 Ollama 重新写向量。

---

## 🎭 Mock 模式

如果没有配置 `LLM_API_KEY`，`get_llm_service()` 会自动返回 `MockLLMService`，提供：
- 固定的饮食建议 JSON（含 `situation_summary` / `recommended_options` / `sleep_friendly_tips` / `one_sentence_summary` 等）
- 固定的"附近餐厅" `tool_call` 响应（仅 mock 层）
- 固定的记忆抽取响应

配置真实的 `LLM_API_KEY` 后，系统会自动切换到 `RealLLMService`（httpx 调 OpenAI-compatible `/chat/completions`）。

---

## 🔧 OpenAI-compatible API 配置

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-endpoint/v1
LLM_MODEL=your-model
```

适用于 OpenAI、LocalAI、VLLM、Azure OpenAI、以及任何兼容 chat-completions 协议的端点。`RealLLMService` 还会把 `system` role 转 `user`（带 `[System]` 前缀），以兼容不支持 system role 的 API。

---

## 📡 主要 API

### 🔐 Auth (`/api/auth`)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册（自动建 `UserFoodProfile`） |
| POST | `/api/auth/login` | 登录，返回 JWT |
| GET  | `/api/auth/me` | 获取当前用户 |
| POST | `/api/auth/logout` | 登出（前端清 token） |

### 👤 Profile (`/api/profile`)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/profile` | 获取用户画像 |
| PUT  | `/api/profile` | 更新用户画像 |
| POST | `/api/profile/init` | 初始化空画像 |

### 🍱 Meals (`/api/meals`)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/meals` | 创建饮食记录 |
| GET  | `/api/meals/today` | 今日饮食 |
| GET  | `/api/meals/recent` | 最近饮食（`limit` 默认 10） |
| GET  | `/api/meals/{meal_id}` | 单条记录 |
| PUT  | `/api/meals/{meal_id}` | 更新 |
| DELETE | `/api/meals/{meal_id}` | 删除 |
| GET  | `/api/meals/summary/daily` | 今日营养摘要 |
| GET  | `/api/meals/summary/weekly` | 近 7 天按日聚合 |

### 🧠 Memories (`/api/memories`)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/memories` | 列表（默认 `status=active`，支持 `memory_type` / `status` 过滤） |
| POST | `/api/memories` | 创建（写完自动 embed） |
| PUT  | `/api/memories/{id}` | 更新（content 变化时自动 re-embed） |
| DELETE | `/api/memories/{id}` | 软删除（status → inactive） |
| DELETE | `/api/memories` | 一键清空（所有 active → inactive） |

### 💬 Advice (`/api/advice`)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/advice/sessions` | 创建会话 |
| GET  | `/api/advice/sessions` | 会话列表 |
| GET  | `/api/advice/sessions/{id}/messages` | 会话消息 |
| PATCH | `/api/advice/sessions/{id}/messages/{msg_id}` | 更新消息（确认 action / memory） |
| DELETE | `/api/advice/sessions/{id}` | 删除会话 |
| POST | `/api/advice/send-stream` | 发送消息，**SSE 流式**（事件：`intent_detected` / `agent_step` / `action_pending` / `memory_pending` / `message_done` / `error`） |
| POST | `/api/advice/restaurant-detail` | 餐厅详情 + LLM 个性化分析 |

### 📈 Records
| 方法 | 路径 | 说明 |
|------|------|------|
| POST/GET/DELETE | `/api/weights` | 体重记录 |
| POST/GET/DELETE | `/api/body-fat` | 体脂记录 |
| POST/GET/DELETE | `/api/trainings` | 训练记录 |

### ⚙️ Users & Health
| 方法 | 路径 | 说明 |
|------|------|------|
| PATCH | `/api/users/auto-memory?auto_memory_enabled={bool}` | 切换自动记忆开关 |
| GET  | `/api/health` | 健康检查 |

---

## 🗄️ 数据库表（PostgreSQL + pgvector）

| 表名 | 说明 |
|------|------|
| `users` | 用户（含 `auto_memory_enabled` 开关） |
| `user_food_profiles` | 用户饮食画像（昵称/性别/身高/体重/体脂/目标/活动等级/训练/偏好/不喜欢/过敏/预算/睡眠） |
| `memory_items` | **长期记忆**（含 `vector(1024)` embedding、`embedding_status` ∈ {pending, ready, failed}、`embedding_updated_at`、JSONB `metadata_json`） |
| `meal_logs` | 饮食记录（餐次/餐时/食物/场景/估算营养/健康分/睡眠影响/AI 评语） |
| `advice_sessions` | AI 会话（含 `scenario`、`is_training_day` (BOOLEAN)） |
| `chat_messages` | 会话消息（含 `action_type` / `action_status` / `action_data` (JSONB)） |
| `weight_records` | 体重记录（`record_date` + `note`） |
| `body_fat_records` | 体脂记录 |
| `training_records` | 训练记录（类型 / 时长 / 强度） |
| `diet_advice_records` | AI 建议记录（结构化 JSONB 字段） |

---

## 🧠 记忆系统（pgvector + 混合排序）

### 1️⃣ 写入路径

每条 `memory_items` 都会同步生成 1024 维 embedding 写入 `embedding` 列。

| 入口 | 行为 |
|------|------|
| `MemoryTools.create_memory` | Agent 自动保存的低重要性记忆；写完调 `embed_memory` |
| `MemoryTools.confirm_memory` | 用户在 UI 上确认的待定记忆；status → active 并强制 re-embed |
| `POST /api/memories` | REST 直写；写完调 `embed_memory`（修复 REST 路径不 embed 的断层） |
| `PUT /api/memories/{id}` | content 变化时调 `embed_memory`（旧向量指向旧 content 的修复） |
| `MemoryTools.backfill_pending_embeddings` | 批量回填 `embedding_status IN ('pending','failed')` 的行 |
| `sql/pg/backfill_embeddings.py` | 一次性 CLI 脚本：扫 `embedding IS NULL OR status != 'ready'` 的全表行 |

embedding 写入失败时把状态置为 `failed`，**不会**让业务写入失败；后续可用 `backfill_embeddings.py` 修复。

### 2️⃣ 召回路径（混合排序）

`MemoryTools.get_relevant_memories(user_id, intent, limit)`：

1. **intent → 限定候选 `memory_type`**
   ```python
   intent_memory_map = {
       "diet_advice":    ["goal", "diet_preference", "food_dislike", "allergy_intolerance",
                          "budget", "sleep", "restriction", "habit"],
       "meal_log":       ["habit", "scenario", "diet_preference"],
       "profile_update": ["goal", "budget", "restriction"],
       "dashboard_query":["goal", "habit", "budget"],
   }
   ```
2. 用 intent 文本做 query，去 Ollama 拿 1024 维向量
3. 在 PG 端用 pgvector 的 `<=>` 余弦距离算 `similarity`
4. **混合分数**（raw SQL 计算）：
   ```
   score = MEMORY_VECTOR_WEIGHT    * (1 - cosine_distance)
         + MEMORY_IMPORTANCE_WEIGHT * (importance_score / 10.0)
   ```
5. embedding 为 NULL 的行：pgvector `<=>` 返回 NULL，`COALESCE` 到 1.0，自然落回纯重要性排序（**冷启动 fallback**）
6. Ollama 不可用 / 抛异常时：自动降级到 ORM 纯重要性排序，**不会**让整次对话炸掉
7. 召回成功后批量更新 `last_used_at = NOW()`

### 3️⃣ 记忆状态机

`memory_items.status` ∈ `{active, pending, inactive, superseded}`

| 规则 | 说明 |
|------|------|
| 高重要性（`allergy_intolerance` / `body_response` / `goal` / `restriction` / `food_dislike`） | 抽出来后**挂起**（`pending`），前端弹卡让用户确认 → `confirm_memory` 写库 |
| 低重要性 | 直接 `create_memory`（`active`） |
| 用户主动改同 type 的偏好 | 旧记忆 `superseded`，新记忆 `active` |
| REST 端 DELETE | 软删除（`inactive`），物理记录保留 |
| `_weight_delta` 等 internal 字段 | 带 `_` 前缀，display 时跳过 |

### 4️⃣ 12 种记忆类型

`diet_preference` · `food_dislike` · `allergy_intolerance` · `goal` · `budget` · `location` · `scenario` · `sleep` · `body_response` · `restriction` · `habit` · `other`

---

## 🤖 Agent 架构

`DietAgentLoop` 使用 ReAct 模式：

1. **多意图检测** — `classify_multi` 用规则 + 优先 LLM 兜底；`memory_candidate` 优先于 `diet_advice` 以优先捕获健康约束
2. **上下文加载（串行）** — 用户画像 → 相关记忆（混合排序）→ 今日饮食 → 最近 10 条会话消息
3. **多 Handler 并行注册** — 信心度 ≥ 0.6 才入队
4. **Pending Action** — 饮食记录 / 资料更新 / 记忆抽取先挂起，前端弹确认卡才落库
5. **ReAct 循环**（通用对话 / 饮食建议） — LLM 可调用工具：

   | 工具 | 说明 |
   |------|------|
   | `map_geocode` | 地址 → 经纬度 |
   | `map_search_places` | 地点搜索 |
   | `map_place_details` | 地点详情 |
   | `search_restaurants` | 一站式搜附近餐厅（带 IP 定位兜底） |
   | `get_restaurant_details` | 餐厅详情 |
   | `get_user_profile` | 读取画像 |
   | `get_today_meals` | 读取今日饮食 |
   | `get_user_memories` | 读取相关记忆（hybrid search） |

   最多 **5 轮**迭代，含渐进式 hint 注入：
   - 连续 2 轮不调用工具 → 工具提醒
   - 剩余 ≤ 2 轮 → 限制提示
   - `map_search_places` 返回 0 结果 → 重试提示（建议改 query）
6. **Memory extraction** — 多意图中含 `MEMORY_CANDIDATE` 时执行；高重要性弹 `memory_confirm` 确认卡，低风险自动保存
7. **Trace** — 21 种 `AgentStep` 枚举（`intent_detected` / `loading_profile` / `loading_memories` / `parsing_meal` / `creating_pending_action` / `react_call_llm` / `react_tool_call` / `react_tool_result` / `react_tool_error` / `react_direct_response` / `react_max_iterations` / `react_hint_progress` …）通过 SSE `agent_step` 事件发给前端 `AgentTracePanel`

### 意图类型

| Intent | 处理 |
|--------|------|
| `MEAL_LOG` | LLM 估算营养 → 创建 `meal_log` pending action |
| `PROFILE_UPDATE` | 规则 + LLM 抽取字段 → 创建 `profile_update` pending action |
| `MEMORY_CANDIDATE` | LLM 抽记忆 → 高重要性弹确认卡 / 低风险自动保存 |
| `DASHBOARD_QUERY` | 返回今日摄入 + 目标分析 |
| `DIET_ADVICE` | 触发 ReAct 通用对话流 |
| `RESTAURANT_SEARCH_PLANNED` | 百度地图搜附近餐厅 → 弹选择卡；或选完餐厅后 LLM 个性化分析 |
| `GENERAL_CHAT` | ReAct 通用对话 |

---

## 🔄 数据迁移（MySQL → PostgreSQL）

仓库保留旧 MySQL 脚本（`init.sql` + `migrations/001..003.sql`），仅作参考。新部署请用 PG 体系。

如果已有 MySQL 数据：
```bash
# 1. 在 PG 上跑 init_pg.sql 建表（含 vector 扩展、CHECK、触发器、索引）
psql -U postgres -h localhost -d eatfit_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
PGPASSWORD=root psql -U postgres -h localhost -d eatfit_ai -f backend/sql/pg/init_pg.sql

# 2. 跑迁移脚本
#    脚本顶部 MYSQL/PG 两个 dict 改成你自己的连接信息再跑；
#    当前仓库默认 MySQL=root/gy7979829@localhost:3306，PG=postgres/root@localhost:5432
cd backend
PYTHONPATH=. python sql/pg/migrate_mysql_to_pg.py

# 3. 回填所有历史 memory 的 embedding（脚本里也硬编码了 PG=postgres/root@localhost:5432，按需改）
PYTHONPATH=. python sql/pg/backfill_embeddings.py
```

迁移脚本会处理：
- MySQL `tinyint(1)` → PG `BOOLEAN`（`is_training_day` / `sleep_sensitive` / `auto_memory_enabled`）
- MySQL `'null'` 字符串 → PG `JSONB NULL`
- 保留原 `id`，并 `setval` 推进 PG 序列
- embedding 列留 NULL，`embedding_status='pending'`，等回填

---

## 🛡️ 安全边界

EatFit AI 严格遵守以下原则：
1. 🚫 **不提供医疗诊断**
2. 🚫 **不鼓励极端节食 / 断食 / 不健康减肥**
3. 🚫 **不承诺快速减肥**
4. 🚫 **不使用攻击性 / 恐吓式文案**（如身材焦虑 / 体重羞耻）
5. ✅ **强调长期习惯而非短期效果**

所有 AI 建议都带 `risk_warnings`（如"以上热量为估算，不等同于精确营养计算"），并提示用户在有特殊情况时咨询医生或营养师。系统 prompt 显式列出 8 条 IMPORTANT RULES + 风险等级（`LOW` / `MEDIUM` / `HIGH`）。

---

## 🙏 致谢

- **[百度地图 MCP](https://github.com/baidu-maps/mcp)** — 提供地理编码 / 地点搜索 / 详情 API 集成，支持附近餐厅推荐
- **[Ollama](https://ollama.com/) + `qwen3-embedding:0.6b`** — 本地嵌入模型，让记忆系统的向量召回完全离线可跑
- **[pgvector](https://github.com/pgvector/pgvector)** — 让 PostgreSQL 原生支持向量检索
- **[FastAPI](https://fastapi.tiangolo.com/)** — 高性能 Python Web 框架
- **[React](https://react.dev/) + [Vite](https://vitejs.dev/)** — 现代前端构建

---

## 📜 许可证

MIT License
