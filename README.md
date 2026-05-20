# EatFit AI - 外食健康饮食助手

EatFit AI 是一个面向普通学生、上班族、健身人群的外食健康饮食 Agent。它帮助用户在经常外食的情况下，做出更健康的饮食选择。

## 🍽️ 功能列表

### 核心功能
- **对话式饮食助手** - 自然语言交互，ReAct 架构的 AI Agent
- **意图识别与分流** - 自动识别饮食记录、资料更新、记忆抽取、餐馆搜索等多种意图
- **多意图并行处理** - 一次对话可同时处理多个意图（如记录饮食 + 提取记忆）
- **饮食记录** - 记录早午晚餐、加餐、训练后补充，自动估算热量和营养素
- **用户画像管理** - 管理身高、体重、目标、预算、饮食偏好、过敏信息等
- **长期记忆系统** - AI 自动从对话中提取用户偏好、习惯，重要记忆需确认，低风险自动保存
- **会话历史管理** - 支持多会话、上下文连续、Session 分组
- **SSE 流式响应** - 实时显示 Agent 推理过程（意图识别、上下文加载、工具调用等步骤）
- **GPS 位置感知** - 可获取用户位置，结合地图工具搜索附近餐厅

### Agent 工具层
- `ProfileTools` - 用户画像读取/更新
- `MemoryTools` - 记忆 CRUD、重要性分级、自动抽取
- `MealTools` - 饮食记录解析、营养估算、今日汇总
- `ChatTools` - 会话消息管理
- `RestaurantTools` - 餐厅搜索（含百度地图 API 集成）
- `MCP Client` - 百度地图地理编码/地点搜索 MCP 工具调用

### 地图集成（百度地图）
- 地址地理编码 (`map_geocode`)
- 地点关键词搜索 (`map_search_places`)
- 地点详情查询 (`map_place_details`)

## 💻 技术栈

### 后端
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.x (ORM)
- Pydantic v2 (数据验证)
- MySQL 8.x
- SSE (Server-Sent Events) 流式响应
- JWT Auth (python-jose + passlib/bcrypt)
- MCP (Model Context Protocol) 客户端

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router v6
- Axios
- dayjs

## 📁 项目目录

```
eatfit-ai/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由 (auth, profile, meals, memories, advice, records)
│   │   ├── core/             # 核心配置 (config, security)
│   │   ├── db/               # 数据库连接 (database.py)
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # 业务服务 (llm_service, advice_service, memory_extractor)
│   │   ├── agent/            # AI Agent (diet_agent_loop, intent_classifier)
│   │   ├── prompts/          # AI Prompt 构建器
│   │   ├── tools/            # Agent 工具层 (profile/memory/meal/chat/restaurant tools, mcp_client)
│   │   └── main.py           # FastAPI 入口
│   ├── sql/
│   │   ├── init.sql          # MySQL 建表语句
│   │   └── migrations/       # 增量迁移脚本
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/              # API 调用封装
│   │   ├── components/chat/  # 聊天相关组件 (ChatMessageList, ChatInput, AgentTracePanel, 各类 ConfirmCard)
│   │   ├── pages/            # 页面 (Landing, Login, Register, Dashboard, Profile, Chat, Meals, Memories, WeeklyReview, Progress)
│   │   ├── types/            # TypeScript 类型定义
│   │   ├── utils/            # 工具函数 (AuthContext, ThemeContext, foodDetection)
│   │   └── App.tsx           # 路由配置
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 🚀 快速启动

### 1. 启动 MySQL

```bash
docker compose up -d mysql
```

### 2. 初始化数据库

方式一：命令行执行
```bash
mysql -uroot -p123456 < backend/sql/init.sql
```

方式二：执行增量迁移（如有）
```bash
mysql -uroot -p123456 < backend/sql/migrations/001_add_chat_messages.sql
mysql -uroot -p123456 < backend/sql/migrations/002_enhance_memory_and_meal_tables.sql
mysql -uroot -p123456 < backend/sql/migrations/003_add_restaurant_context.sql
```

### 3. 配置后端环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/eatfit_ai?charset=utf8mb4

JWT_SECRET_KEY=please-change-this-secret-key-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# 百度地图（可选，用于餐馆搜索）
BAIDU_MAP_AK=your-baidu-map-api-key

FRONTEND_ORIGIN=http://localhost:5173
```

### 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

后端运行在 http://localhost:8000

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

## 🎭 Mock 模式

如果没有配置 `LLM_API_KEY`，系统会自动使用 MockLLMService，返回预设的示例数据。

这意味着你可以在不消耗任何 API 额度的情况下：
- 测试注册/登录流程
- 测试页面导航
- 测试饮食记录
- 测试记忆功能

配置真实的 `LLM_API_KEY` 后，系统会自动切换到真实 AI 服务。

## 🔧 OpenAI-compatible API 配置

如果你有其他 OpenAI-compatible API（如 LocalAI、VLLM、Azure 等），可以配置：

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-api-endpoint/v1
LLM_MODEL=your-model
```

## 📡 主要 API

### Auth
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 获取当前用户
- `POST /api/auth/logout` - 登出

### Profile
- `GET /api/profile` - 获取用户画像
- `PUT /api/profile` - 更新用户画像

### Meals
- `POST /api/meals` - 创建饮食记录
- `GET /api/meals/today` - 获取今日饮食
- `GET /api/meals/recent` - 获取最近饮食记录
- `GET /api/meals/summary/daily` - 获取每日营养摘要
- `GET /api/meals/summary/weekly` - 获取每周营养摘要
- `PUT /api/meals/{id}` - 更新饮食记录
- `DELETE /api/meals/{id}` - 删除饮食记录

### Advice / Chat
- `POST /api/advice/send` - 发送消息（同步）
- `POST /api/advice/send-stream` - 发送消息（SSE 流式，支持 Agent 推理过程实时推送）
- `POST /api/advice/sessions` - 创建会话
- `GET /api/advice/sessions` - 获取会话列表
- `GET /api/advice/sessions/{id}/messages` - 获取会话消息
- `PATCH /api/advice/sessions/{id}/messages/{msg_id}` - 更新消息状态（如确认操作）
- `DELETE /api/advice/sessions/{id}` - 删除会话

### Memories
- `GET /api/memories` - 获取记忆列表
- `POST /api/memories` - 创建记忆
- `PUT /api/memories/{id}` - 更新记忆
- `DELETE /api/memories/{id}` - 删除记忆
- `DELETE /api/memories` - 清空所有记忆

### Records
- `POST /api/records/weights` - 记录体重
- `GET /api/records/weights` - 获取体重记录
- `POST /api/records/body-fat` - 记录体脂
- `GET /api/records/body-fat` - 获取体脂记录
- `POST /api/records/trainings` - 记录训练
- `GET /api/records/trainings` - 获取训练记录

## 🗄️ 数据库表

| 表名 | 说明 |
|------|------|
| `users` | 用户表（含 auto_memory_enabled 开关） |
| `user_food_profiles` | 用户饮食画像 |
| `memory_items` | 长期记忆 |
| `meal_logs` | 饮食记录 |
| `advice_sessions` | AI 会话（含 scenario、is_training_day、restaurant_context） |
| `chat_messages` | 会话消息（含 action_type/action_status/action_data 供确认操作） |
| `diet_advice_records` | AI 建议记录 |
| `weight_records` | 体重记录 |
| `body_fat_records` | 体脂记录 |
| `training_records` | 训练记录 |

## 🤖 Agent 架构

DietAgentLoop 使用 ReAct 模式：

1. **意图检测** (`IntentClassifier`) - 规则 + LLM 多意图分类
2. **上下文加载** - 并行加载用户画像、记忆、今日饮食、会话历史
3. **多 Handler 执行** - 按意图类型分发到不同处理器
4. **Pending Action** - 需要确认的操作（饮食记录、资料更新）先挂起，用户确认后才写入数据库
5. **ReAct 循环** - 通用对话中 LLM 可调用工具（地图搜索、获取上下文等）

意图类型：
- `MEAL_LOG` - 记录饮食
- `PROFILE_UPDATE` - 更新资料
- `MEMORY_CANDIDATE` - 提取记忆
- `DASHBOARD_QUERY` - 查询今日摘要
- `DIET_ADVICE` - 饮食建议
- `RESTAURANT_SEARCH_PLANNED` - 餐馆搜索
- `GENERAL_CHAT` - 通用对话

## 🛡️ 安全边界

EatFit AI 严格遵守以下原则：
1. 不提供医疗诊断
2. 不鼓励极端节食
3. 不承诺快速减肥
4. 不使用攻击性文案
5. 强调长期习惯而非短期效果

所有 AI 建议都带有安全边界提醒，建议用户在有特殊情况时咨询医生或营养师。

## 🙏 致谢

- **[百度地图 MCP](https://github.com/baidu-maps/mcp)** - 提供地理编码和地点搜索 API 集成，支持餐厅搜索功能

## 📜 许可证

MIT License