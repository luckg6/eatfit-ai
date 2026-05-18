# EatFit AI Memory 架构说明

> 本文件描述 Memory 架构的**设计意图和现状**，供后续开发参考。

---

## 1. 项目现状

### 1.1 已完成

- [x] `chat_messages` 表 — 多轮聊天消息持久化
- [x] SSE 流式输出 — `/api/advice/send-stream`
- [x] `DietAgentLoop` — ReAct 风格 Agent 主循环
- [x] `IntentClassifier` — 规则优先 + LLM 兜底
- [x] 意图类型: `meal_log`, `diet_advice`, `profile_update`, `memory_candidate`, `dashboard_query`, `general_chat`, `restaurant_search_planned`
- [x] 确认卡机制 — `MealLogConfirmCard`, `ProfileUpdateConfirmCard`, `MemoryConfirmCard`
- [x] `MemoryTools.create_pending_memory()` — 高重要记忆生成确认卡
- [x] `MemoryExtractor` — 主动记忆提取 (关键词触发)
- [x] `Memories.tsx` — Memory Center 查看/编辑/禁用/启用
- [x] `memory_items` 增强 — status, confidence_score, source_message_id, last_used_at, metadata_json
- [x] `meal_logs` 增强 — calorie_confidence, nutrition_source, source_message_id
- [x] 软删除 — 旧记忆 `status = superseded/inactive`，不物理删除

### 1.2 待做

- [ ] Memory Consolidation — 每日/会话结束后的记忆整合
- [ ] 向量语义检索 — Qdrant pgvector 等
- [ ] 知识库 RAG — 外部文档增强
- [ ] 餐馆搜索 MCP — 百度地图/外卖商家搜索
- [ ] 多意图 (multi-intent) 支持

---

## 2. 核心数据结构

### 2.1 各表职责

| 表 | 职责 | 说明 |
|---|---|---|
| `users` | 用户账号 | `auto_memory_enabled` 控制是否自动提取记忆 |
| `user_food_profiles` | 强结构化用户画像 | 用于计算: 体重/身高/目标/预算等 |
| `memory_items` | 半结构化长期记忆 | 偏好/禁忌/习惯/场景等 |
| `meal_logs` | 已确认的餐食记录 | 用户确认后写入 |
| `chat_messages` | 聊天消息 | 含 `action_type/action_status/action_data` |
| `advice_sessions` | 会话元信息 | 标题/创建时间 |
| `diet_advice_records` | AI 建议结构化结果 | 不直接用于 Memory |
| `weight_records` | 体重记录 | 时间序列 |
| `body_fat_records` | 体脂记录 | 时间序列 |
| `training_records` | 训练记录 | 时间序列 |

### 2.2 memory_items 字段

```sql
id, user_id, memory_type, content,
importance_score, -- 1-10
status, -- active / inactive / superseded / pending
confidence_score, -- 0.00-1.00
source, -- manual / auto_extracted / chat
source_message_id, -- 来源消息
last_used_at, -- 最近召回时间
metadata_json, -- 额外数据
created_at, updated_at
```

### 2.3 memory_type 枚举值

> 与 `backend/app/tools/memory_tools.py` 保持一致

```
diet_preference      饮食偏好
food_dislike         不喜欢的食物
allergy_intolerance  过敏/不耐受
goal                 长期目标
budget               预算偏好
location             常用位置
scenario             常见饮食场景
sleep                睡眠相关
body_response        身体反应
restriction          现实限制
habit                饮食习惯
other                其他
```

### 2.4 高重要记忆类型 (需要确认)

> 定义在 `MemoryTools.HIGH_IMPORTANCE_TYPES`

```
allergy_intolerance  过敏/不耐受
body_response        身体反应
goal                 长期目标
restriction          现实限制
```

---

## 3. 记忆提取策略

### 3.1 规则优先 + LLM 兜底

不要每轮对话都调用 LLM 抽取记忆。

```
用户输入
  ↓
关键词规则初筛 (MEMORY_TRIGGERS)
  ↓
判断是否可能包含长期记忆
  ↓
必要时 LLM 结构化提取
  ↓
根据 memory_type 决定是否需要确认
  ↓
写入 memory_items
```

### 3.2 可触发记忆提取的表达

见 `backend/app/agent/intent_classifier.py` 中的 `MEMORY_TRIGGERS`:

- `我喜欢...` / `我不喜欢...` → diet_preference / food_dislike
- `我不能吃...` / `过敏...` → allergy_intolerance
- `想(增肌|减脂|维持)` → goal
- `(咖啡|茶|奶茶).*睡不着` → sleep
- `没有厨房` / `主要外食` → restriction
- 等等

### 3.3 记忆分类写入规则

| 用户表达 | 存储位置 |
|---|---|
| 我刚吃了牛肉饭 | `meal_logs` (确认后) |
| 我现在体重 58kg | `user_food_profiles` / `weight_records` (确认后) |
| 我喝牛奶容易拉肚子 | `memory_items` (高重要，需确认) |
| 我想以后少油少糖 | `memory_items` (低风险，可自动) |
| 我一顿饭预算 25 元 | `user_food_profiles` + `memory_items` |
| 我常在学校附近吃饭 | `memory_items` (location/scenario) |
| 我今晚不知道吃什么 | `chat_messages` (不写长期记忆) |

---

## 4. Agent 三层结构

### 4.1 前置: 意图识别

见 `IntentClassifier`:

```
meal_log             用户记录吃了什么
diet_advice          用户请求饮食建议
profile_update       用户更新基础信息
memory_candidate     用户提到可能需要长期记忆的信息
dashboard_query      用户查询今日摄入
general_chat         普通闲聊
restaurant_search_planned 餐馆搜索 (P2)
```

### 4.2 Agent Loop 工具

见 `backend/app/tools/`:

```
get_user_profile       获取用户画像
get_recent_memories    获取相关记忆
get_today_meals        获取今日餐食
create_meal_log_pending  创建餐食待确认
confirm_meal_log       确认餐食记录
create_profile_update_pending  创建资料更新待确认
confirm_profile_update  确认资料更新
create_memory_pending   创建记忆待确认
confirm_memory          确认记忆
```

### 4.3 后置: 记忆抽取

见 `MemoryExtractor`:

```
用户消息 + AI 回复
  ↓
关键词触发提取
  ↓
检查是否已存在
  ↓
过滤重复偏好 (噪音过滤)
  ↓
低风险 → 自动写入
高重要 → 生成确认卡
```

---

## 5. 软删除与状态管理

### 5.1 状态值

```
active      激活使用中
inactive    已禁用
superseded  被新记忆替代
pending     待确认
```

### 5.2 原则

- 不物理删除旧记忆
- 目标变更时: 旧记忆 `status = superseded`，新记忆 `status = active`
- 用户禁用时: `status = inactive`
- 用户删除 Memory Center 中的记忆时: `status = inactive`

---

## 6. 阶段规划

### 阶段 0: 聊天上下文 ✅ 已完成

- chat_messages 表
- SSE 流式输出
- 会话管理

### 阶段 1: 结构化长期记忆 ✅ 已完成

- memory_items 增强字段
- 确认卡机制
- Memory Center

### 阶段 2: 记忆整合 🔲 待做

- 每日/会话结束后 LLM 整合
- 去重/合并/冲突处理

### 阶段 3: 向量语义检索 🔲 待做

- Qdrant / pgvector 接入
- 跨类型语义召回

### 阶段 4: 知识库 RAG 🔲 待做

- 外部文档增强
- 膳食指南等静态知识

---

## 7. 当前架构图

```
用户输入
    ↓
IntentClassifier (规则优先)
    ↓
DietAgentLoop (ReAct)
    ├── ProfileTools.get_user_profile()
    ├── MemoryTools.get_relevant_memories()
    ├── MealTools.get_today_meals()
    ├── MealTools.create_pending_meal_action()
    ├── ProfileTools.create_pending_update()
    └── MemoryTools.create_pending_memory()
    ↓
SSE 流式输出
    ↓
前端渲染 + 确认卡交互
    ↓
用户确认 → 写入对应表
    ↓
MemoryExtractor (异步) → 候选记忆提取
```

---

## 8. 前端组件结构

```
pages/
  Chat.tsx              主聊天页面
  Memories.tsx          Memory Center

components/chat/
  ChatMessageList.tsx
  ChatInput.tsx
  ChatContextBar.tsx
  MealLogConfirmCard.tsx
  ProfileUpdateConfirmCard.tsx
  MemoryConfirmCard.tsx
  AgentTracePanel.tsx

api/
  adviceAPI.sendMessageStream()  SSE
  memoriesAPI.list/create/update/delete
  mealsAPI.create/getToday
  profileAPI.get/update
```

---

## 9. 后端模块结构

```
app/
  agent/
    diet_agent_loop.py      Agent Loop
    intent_classifier.py    意图识别

  tools/
    profile_tools.py
    memory_tools.py
    meal_tools.py
    chat_tools.py

  services/
    memory_extractor.py     主动记忆提取
    advice_service.py
    llm_service.py

  models/
    memory.py               MemoryItem 模型
    chat_message.py        ChatMessage 模型
    advice.py               AdviceSession 模型

  api/
    advice.py               SSE + 会话管理
    memories.py             Memory CRUD
    meals.py
    profile.py
```

---

## 10. 不该做的事情

```
✗ 每轮对话都调用 LLM 抽取记忆
✗ 把临时信息写入 memory_items
✗ 把单次餐食当长期记忆
✗ 静默修改用户重要资料
✗ 物理删除旧记忆
✗ 一开始上向量库
✗ 把知识库 RAG 和用户 Memory 混为一谈
```
