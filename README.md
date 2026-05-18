# EatFit AI - 外食健康饮食助手

EatFit AI 是一个面向普通学生、上班族、健身人群的外食健康饮食 Agent。它帮助用户在经常外食的情况下，做出更健康的饮食选择。

## 功能列表

### 核心功能
- **用户注册/登录** - JWT 认证，密码加密存储
- **用户健康饮食画像** - 管理身高、体重、体脂率、目标、饮食偏好等
- **饮食咨询** - AI 根据用户情况推荐饮食选择
- **饮食记录** - 记录早午晚餐、加餐、训练后补充等
- **长期记忆** - AI 学习用户的偏好、习惯、训练和睡眠特点
- **每日饮食建议** - 根据用户目标生成每日三餐建议
- **一周饮食复盘** - 回顾本周饮食、蛋白质摄入、训练情况

### MCP-ready 工具层
- `memory_tool` - 记忆管理
- `nutrition_tool` - 营养估算
- `meal_log_tool` - 饮食记录
- `profile_tool` - 用户画像
- `recommendation_tool` - 推荐服务

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- MySQL 8.x
- JWT Auth
- Passlib / bcrypt

### 前端
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

## 项目目录

```
eatfit-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置（config, security）
│   │   ├── db/           # 数据库连接
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # 业务服务（LLM, Advice）
│   │   ├── prompts/      # AI Prompt 构建器
│   │   ├── tools/        # MCP-ready 工具层
│   │   └── main.py       # FastAPI 入口
│   ├── sql/
│   │   └── init.sql      # MySQL 建表语句
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/          # API 调用
│   │   ├── components/
│   │   ├── pages/        # 页面组件
│   │   ├── routes/
│   │   ├── types/        # TypeScript 类型
│   │   └── utils/        # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 快速启动

### 1. 启动 MySQL

```bash
docker compose up -d mysql
```

### 2. 初始化数据库

方式一：命令行执行
```bash
mysql -uroot -p123456 < backend/sql/init.sql
```

方式二：Navicat 手动执行
1. 连接本地 MySQL
2. 新建查询
3. 打开 `backend/sql/init.sql`
4. 执行全部 SQL

### 3. 配置后端环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件（可选，使用默认配置即可）：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/eatfit_ai?charset=utf8mb4

JWT_SECRET_KEY=please-change-this-secret-key-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

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

## Mock 模式

如果没有配置 `LLM_API_KEY`，系统会自动使用 MockLLMService，返回预设的示例数据。

这意味着你可以在不消耗任何 API 额度的情况下：
- 测试注册/登录流程
- 测试页面导航
- 测试饮食记录
- 测试记忆功能

配置真实的 `LLM_API_KEY` 后，系统会自动切换到真实 AI 服务。

## OpenAI-compatible API 配置

如果你有其他 OpenAI-compatible API（如 LocalAI、VLLM、Azure 等），可以配置：

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-api-endpoint/v1
LLM_MODEL=your-model
```

## MCP-ready 说明

当前实现是 MCP-ready 工具层，后续可以轻松拆分成独立的 MCP Server：

```
tools/
├── memory_tool.py      -> MCP Server: memory-server
├── nutrition_tool.py   -> MCP Server: nutrition-server
├── meal_log_tool.py    -> MCP Server: meal-log-server
├── profile_tool.py     -> MCP Server: profile-server
└── recommendation_tool.py -> MCP Server: recommendation-server
```

未来可以接入：
- 地图 MCP - 获取附近餐厅
- 外卖菜单 MCP - 获取外卖菜单
- 运动健康 MCP - 同步运动数据
- 日历 MCP - 同步日程安排

## 主要 API

### Auth
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 获取当前用户
- `POST /api/auth/logout` - 登出

### Profile
- `GET /api/profile` - 获取用户画像
- `PUT /api/profile` - 更新用户画像
- `POST /api/profile/init` - 初始化用户画像

### Advice
- `POST /api/advice/generate` - 生成饮食建议
- `GET /api/advice/history` - 获取建议历史
- `POST /api/advice/daily-plan` - 生成每日计划
- `POST /api/advice/weekly-review` - 生成周报

### Meals
- `POST /api/meals` - 创建饮食记录
- `GET /api/meals/today` - 获取今日饮食
- `GET /api/meals/summary/daily` - 获取每日营养摘要
- `GET /api/meals/summary/weekly` - 获取每周营养摘要

### Memories
- `GET /api/memories` - 获取记忆列表
- `POST /api/memories` - 创建记忆
- `PUT /api/memories/{id}` - 更新记忆
- `DELETE /api/memories/{id}` - 删除记忆
- `DELETE /api/memories` - 清空所有记忆

### Records
- `POST /api/weights` - 记录体重
- `GET /api/weights` - 获取体重记录
- `POST /api/body-fat` - 记录体脂
- `GET /api/body-fat` - 获取体脂记录
- `POST /api/trainings` - 记录训练
- `GET /api/trainings` - 获取训练记录

## 后续迭代方向

### 功能扩展
1. 真实 AI 接入 - 支持更多 LLM 提供商
2. 会员系统 - 额度限制、付费功能
3. 体重/体脂图表 - 可视化追踪
4. 社交功能 - 分享饮食记录

### MCP 扩展
1. 地图集成 - 附近餐厅推荐
2. 外卖平台集成 - 自动获取菜单
3. 运动设备集成 - Apple Watch、Garmin 等
4. 日历集成 - 训练日程提醒

### 数据分析
1. 营养趋势分析
2. 目标进度追踪
3. 个性化报告

## 安全边界

EatFit AI 严格遵守以下原则：
1. 不提供医疗诊断
2. 不鼓励极端节食
3. 不承诺快速减肥
4. 不使用攻击性文案
5. 强调长期习惯而非短期效果

所有 AI 建议都带有安全边界提醒，建议用户在有特殊情况时咨询医生或营养师。

## 许可证

MIT License