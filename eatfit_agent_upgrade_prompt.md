# EatFit AI 健康饮食 Agent 项目改造提示词

> 这份提示词用于直接发给 Claude Code。目标是基于现有项目做渐进式改造，不推倒重来，重点强化：少表单聊天交互、长期记忆、餐食记录确认、SSE 流式输出、后端工具调用、清晰代码结构。

---

## 一、项目定位

请你先完整阅读当前项目结构、前后端代码、数据库初始化 SQL、已有 API、已有页面和组件，然后在现有项目基础上进行渐进式改造。

这是一个面向 **学生 / 年轻上班族外食场景** 的健康饮食 Agent，重点解决：

1. 今天吃什么；
2. 怎么吃更健康；
3. 如何低成本记录饮食；
4. 如何通过长期记忆越用越懂用户；
5. 如何尽量减少表单，让用户通过自然语言完成大部分操作。

这个项目不是简单的“AI 饮食建议问答页面”，而是要改造成一个更像 ChatGPT / Agent 的健康饮食助手。

项目核心卖点：

1. 少填表单，尽量通过聊天完成大部分操作；
2. 长期记忆，越用越懂用户；
3. 外食场景优先，包括学校食堂、便利店、快餐、餐馆、外卖等；
4. 后续支持餐厅搜索 / 外卖搜索 MCP；
5. Agent Loop 内部支持工具调用、ReAct 风格执行过程和可视化展示；
6. 保留 Dashboard 和 Profile 页面，但 Advice 页面要改造成聊天入口。

---

## 二、当前已有数据库基础

请基于当前已有数据库表做改造，不要重做数据库。

当前已有核心表大致包括：

- `users`：用户表，其中 `auto_memory_enabled` 控制是否开启自动记忆；
- `user_food_profiles`：用户基础饮食画像；
- `memory_items`：长期 / 半长期记忆；
- `meal_logs`：饮食记录；
- `advice_sessions`：建议 / 对话会话；
- `diet_advice_records`：结构化饮食建议记录；
- `weight_records`、`body_fat_records`、`training_records`：身体和训练记录。

本阶段训练相关功能先弱化，不作为重点，不要把系统复杂度扩散到训练计划上。

---

## 三、整体架构要求

请采用三层结构：

```text
用户输入
↓
Agent Loop 之前：粗粒度意图识别，用于路由
↓
Agent Loop 内部：ReAct 风格主循环，负责工具调用、上下文获取、建议生成
↓
Agent Loop 之后：后置记忆抽取、结构化数据沉淀、状态更新
```

不要把所有意图识别都塞进 Agent Loop。

---

## 四、第一阶段改造范围

第一阶段不要一次性做太大。优先完成以下内容：

1. Advice 页面改造成 ChatGPT 风格聊天界面；
2. 新增多轮聊天消息持久化；
3. 增加粗粒度意图识别；
4. 增加后端工具层；
5. 增加餐食记录确认卡；
6. 增加基础资料更新确认卡；
7. 增强 memory_items 表；
8. 增加 Memory Center 记忆管理页面；
9. 支持 SSE 流式输出和 Agent 执行过程展示；
10. 生成一个二阶段 TODO 文档，记录百度地图 MCP / 餐馆搜索 / 外卖搜索能力。

---

## 五、暂不做或弱化的内容

第一阶段暂时不要实现：

1. 百度地图 MCP 餐馆搜索；
2. 美团 / 外卖商家 MCP 搜索；
3. 向量数据库；
4. 多意图拆解执行；
5. 复杂训练计划；
6. 复杂营养数据库；
7. 复杂推荐算法。

这些可以写入待做清单，但不要在第一阶段强行实现。

---

## 六、数据库改造要求

### 6.1 新增 chat_messages 表

当前 `advice_sessions` 更像一次建议记录，不适合保存多轮聊天消息。

请新增一张 `chat_messages` 表，用于保存每条用户 / 助手消息，以及消息中附带的 pending action。

请新增 SQL 文件，例如：

```text
database/migrations/xxx_add_chat_messages_and_memory_enhancement.sql
```

建议表结构如下，具体命名可按当前项目规范调整：

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,

  -- 用于保存确认卡动作，例如 meal_log、profile_update、memory_confirm
  action_type VARCHAR(64),
  action_status VARCHAR(64),
  action_data JSON,

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_chat_messages_session
    FOREIGN KEY (session_id) REFERENCES advice_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_chat_messages_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

  KEY idx_chat_messages_session_id (session_id),
  KEY idx_chat_messages_user_id (user_id),
  KEY idx_chat_messages_created_at (created_at),
  KEY idx_chat_messages_action_status (action_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

字段说明：

- `role`：`user` / `assistant` / `system` / `tool`；
- `content`：消息文本；
- `action_type`：如 `meal_log`、`profile_update`、`memory_confirm`；
- `action_status`：如 `pending`、`confirmed`、`cancelled`、`executed`；
- `action_data`：保存确认卡需要的数据。

---

### 6.2 小幅增强 memory_items 表

不要重做 memory 模块，只在现有 `memory_items` 表基础上增强。

建议增加字段：

```sql
ALTER TABLE memory_items
  ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active' AFTER source,
  ADD COLUMN confidence_score DECIMAL(4,2) DEFAULT 0.80 AFTER importance_score,
  ADD COLUMN source_message_id BIGINT NULL AFTER source,
  ADD COLUMN last_used_at DATETIME NULL AFTER updated_at,
  ADD COLUMN metadata_json JSON NULL AFTER last_used_at;
```

字段说明：

- `status`：
  - `active`：有效记忆；
  - `inactive`：用户删除 / 禁用；
  - `superseded`：被新记忆取代；
  - `pending`：等待用户确认；
- `confidence_score`：记忆置信度；
- `source_message_id`：来自哪条聊天消息；
- `last_used_at`：最近一次被召回使用的时间；
- `metadata_json`：额外信息，例如来源、触发词、是否需要确认、冲突记忆 id 等。

注意：

1. 不要物理删除旧记忆；
2. 用户删除时改为 `inactive`；
3. 发生冲突时将旧记忆标记为 `superseded`；
4. 查询时默认只查 `status = 'active'` 的记忆。

---

### 6.3 小幅增强 meal_logs 表

MVP 阶段热量、蛋白质、碳水、脂肪用 LLM 估算，但必须明确标注是估算值。

建议增加字段：

```sql
ALTER TABLE meal_logs
  ADD COLUMN calorie_confidence DECIMAL(4,2) DEFAULT 0.70 AFTER estimated_fat,
  ADD COLUMN nutrition_source VARCHAR(64) DEFAULT 'llm_estimate' AFTER calorie_confidence,
  ADD COLUMN source_message_id BIGINT NULL AFTER nutrition_source;
```

字段说明：

- `calorie_confidence`：热量估算置信度；
- `nutrition_source`：如 `llm_estimate`、`manual`、`food_database`；
- `source_message_id`：来自哪条聊天消息。

---

## 七、表职责划分

请保持下面的职责边界：

```text
chat_messages
保存“聊了什么”，用于恢复多轮聊天记录和展示确认卡。

meal_logs
保存“用户确认自己实际吃了什么”。

user_food_profiles
保存强结构化、稳定、用于计算的用户基础画像。
例如：性别、年龄、身高、体重、目标体重、主要目标、预算、过敏字段等。

memory_items
保存语义强但更灵活的长期 / 半长期画像。
例如：用户晚饭吃太油会影响睡眠、用户经常在学校食堂吃饭、用户偏好高蛋白外食等。

advice_sessions
保存一次聊天会话的元信息。
例如：user_id、title、context_text、created_at。

diet_advice_records
保存一次 AI 饮食建议的结构化结果，方便后续统计和复盘。

Dashboard
仍然作为完整数据页保留。

Advice / Chat 页面
作为主要交互入口，只展示轻量上下文摘要。
```

---

## 八、Advice 页面改造要求

将 `Advice` 页面改造成 ChatGPT 风格界面。

### 8.1 页面布局

建议结构：

```text
顶部：轻量上下文栏
中间：聊天消息列表
底部：输入框
右侧或抽屉：可选显示 Agent 执行过程 / 记忆召回 / 工具调用过程
```

轻量上下文栏展示：

```text
今日热量
今日蛋白质
今日餐数
当前目标
预算
关键记忆 2~3 条
```

不要把 Dashboard 整页搬到 Advice 页面。

Dashboard 当前保留，后续再逐渐把关键能力折叠进 Chat 页面中。

---

### 8.2 聊天组件建议

请按职责拆分组件，不要把所有代码写进一个巨大文件。

建议前端目录：

```text
src/components/chat/
  ChatMessageList.tsx
  ChatMessageBubble.tsx
  ChatInput.tsx
  ChatContextBar.tsx
  AgentTracePanel.tsx
  MealLogConfirmCard.tsx
  ProfileUpdateConfirmCard.tsx
  MemoryConfirmCard.tsx

src/pages/
  Advice.tsx
  MemoryCenter.tsx
```

组件职责：

- `ChatMessageList`：滚动消息列表，自动滚动到底部；
- `ChatMessageBubble`：用户 / 助手气泡；
- `ChatInput`：自增高输入框，Enter 发送，Shift+Enter 换行；
- `ChatContextBar`：显示今日轻量摘要；
- `AgentTracePanel`：显示工具调用、MCP 调用、记忆召回等过程；
- `MealLogConfirmCard`：餐食记录确认卡；
- `ProfileUpdateConfirmCard`：基础资料更新确认卡；
- `MemoryConfirmCard`：高重要记忆确认卡；
- `MemoryCenter`：记忆查看、编辑、禁用页面。

---

## 九、意图识别要求

### 9.1 粗粒度意图分类

Agent Loop 之前做粗粒度意图识别，用于路由。

第一阶段支持这些主意图：

```text
meal_log          用户记录吃了什么
diet_advice       用户请求饮食建议
profile_update    用户更新基础资料
memory_candidate  用户提到可能需要长期记忆的信息
dashboard_query   用户查询今日摄入、餐食记录、目标等数据
general_chat      普通闲聊
```

先不要做：

```text
weight_log
body_fat_log
sleep_note
```

体重、体脂、睡眠相关内容第一阶段可以归到：

```text
profile_update
memory_candidate
general_chat
```

第二阶段预留：

```text
restaurant_search  餐厅 / 外食地点搜索
takeout_search      外卖商家搜索
```

但第一阶段不要实现地图 / 外卖 MCP，只写入 TODO 文档。

---

### 9.2 意图识别策略

请采用：

```text
规则优先 + LLM 兜底
```

示例：

```text
“我刚吃了牛肉饭”
→ 规则识别为 meal_log

“中午点了麻辣烫”
→ 规则识别为 meal_log

“我晚上吃什么比较好”
→ 可规则或 LLM 识别为 diet_advice

“我现在体重 58kg”
→ 识别为 profile_update

“我不太能喝牛奶，喝了会拉肚子”
→ 识别为 memory_candidate，可能同时触发高重要记忆确认

“今天吃了多少热量？”
→ 识别为 dashboard_query

“附近有没有适合减脂吃的餐馆？”
→ 第一阶段识别为 restaurant_search_planned，然后友好回复：餐馆搜索会在二阶段接入地图 MCP，目前可让用户手动描述附近选项，系统先帮他判断。
```

MVP 先支持主意图，不做 multi-intent 拆解。

如果一句话中包含多个意图，先选择最主要的意图，并在回复中自然提示用户可以继续补充。

---

## 十、Agent Loop 要求

### 10.1 Agent Loop 位置

Agent Loop 是主循环，但不要承担所有路由工作。

流程：

```text
handleUserMessage(text)
↓
保存用户消息到 chat_messages
↓
规则优先 + LLM 兜底识别 intent
↓
根据 intent 进入对应 Agent 执行流程
↓
Agent Loop 内部 ReAct 风格调用后端 tools
↓
SSE 输出过程与最终回复
↓
保存 assistant 消息到 chat_messages
↓
后置 memory extraction
```

---

### 10.2 Agent Loop 内部职责

Agent Loop 内部负责任务执行级决策：

```text
是否查询 user_food_profiles
是否查询 memory_items
是否查询今日 meal_logs
是否查询最近 chat_messages
是否创建 pending action
是否调用 LLM 估算营养
是否生成饮食建议
是否触发记忆抽取
```

Agent Loop 内部要体现 ReAct 思想：

```text
Thought: 用户想知道晚上吃什么，需要先获取今日饮食和长期偏好。
Action: get_user_profile
Observation: 用户目标是减脂，预算 25 元，偏好高蛋白。
Action: get_today_meals
Observation: 用户今天午餐吃了牛肉饭，蛋白质尚可，脂肪偏高。
Action: get_relevant_memories
Observation: 用户睡眠较浅，晚餐不适合太油太辣。
Final Answer: 建议晚餐选择……
```

注意：不要把模型内部思考原文直接暴露给用户。前端展示时可以展示简化版 Agent 过程，例如：

```text
正在读取你的饮食画像……
正在查看今日已记录餐食……
正在召回相关记忆……
正在生成晚餐建议……
```

---

## 十一、后端 Tool 设计要求

所有核心工具尽量放在后端，不要让前端承担太多业务逻辑。

建议后端工具层按模块拆分：

```text
tools/
  profile_tools
  memory_tools
  meal_tools
  advice_tools
  chat_tools
  dashboard_tools
```

工具建议：

```text
get_user_profile(user_id)
获取 user_food_profiles。

get_relevant_memories(user_id, intent, limit)
按 memory_type、importance_score、updated_at 获取 active 记忆。

get_today_meals(user_id)
获取今日 meal_logs。

get_recent_chat_messages(session_id, limit)
获取当前会话最近若干条消息。

parse_meal_from_text(text, context)
从用户文本中解析餐食、餐别、估算热量和宏量营养。

create_pending_meal_action(session_id, user_id, parsed_meal)
创建待确认餐食动作，写入 chat_messages.action_data。

confirm_meal_log(action_message_id)
用户确认后写入 meal_logs，并更新 chat_messages.action_status = confirmed。

parse_profile_update(text)
解析用户想更新的结构化基础信息。

create_pending_profile_update(session_id, user_id, parsed_update)
创建基础资料更新确认卡。

confirm_profile_update(action_message_id)
用户确认后更新 user_food_profiles。

extract_memory_candidates(user_id, session_id, message)
后置记忆抽取。

create_memory_item(user_id, memory)
写入 memory_items。

mark_memory_inactive(memory_id)
用户在 Memory Center 中禁用记忆。

update_memory_item(memory_id, content, memory_type, importance_score)
用户编辑记忆。

get_chat_context_for_advice(user_id, session_id)
聚合画像、记忆、今日餐食、最近消息，生成 advice prompt 上下文。
```

---

## 十二、餐食记录流程

用户说：

```text
我刚吃了牛肉饭
```

系统流程：

```text
1. 保存用户消息到 chat_messages。
2. 前置意图识别为 meal_log。
3. Agent Loop 调用 parse_meal_from_text。
4. LLM 估算：
   - food_text：牛肉饭
   - meal_type：lunch / dinner / unknown
   - estimated_calories：例如 650
   - estimated_protein：例如 28
   - estimated_carbs：例如 85
   - estimated_fat：例如 22
   - calorie_confidence：例如 0.65
   - nutrition_source：llm_estimate
5. assistant 回复中展示 MealLogConfirmCard。
6. 用户点击确认。
7. 后端写入 meal_logs。
8. 更新对应 chat_messages.action_status = confirmed。
9. Dashboard 和 ChatContextBar 能看到今日数据更新。
```

注意：

1. 餐食记录不要自动写入 `meal_logs`；
2. 必须用户确认后才写入；
3. 热量和营养必须标注为“估算值”；
4. 单次餐食不要直接写入 `memory_items`；
5. 只有反复出现或用户明确表达长期偏好时，才写入长期记忆。

---

## 十三、基础资料更新流程

用户说：

```text
我现在体重 58kg
```

系统流程：

```text
1. 意图识别为 profile_update。
2. 解析出字段：weight_kg = 58。
3. 不要直接更新 user_food_profiles。
4. 生成 ProfileUpdateConfirmCard：
   “检测到你想更新体重为 58kg，是否确认？”
   [确认] [取消]
5. 用户确认后，更新 user_food_profiles.weight_kg。
6. 如果当前项目已有 weight_records，也可以同步写入 weight_records，注意不要破坏现有逻辑。
```

用户说：

```text
我预算一顿最好控制在 25 元以内
```

系统流程：

```text
1. 解析为 profile_update。
2. 生成确认卡。
3. 用户确认后更新 user_food_profiles.budget_per_meal = 25。
```

用户说：

```text
我主要想减脂，但不想饿肚子
```

系统流程：

```text
1. 可能是 profile_update + memory_candidate。
2. MVP 先按主意图处理。
3. 如果更新 primary_goal，需要确认。
4. “不想饿肚子”可以作为低风险记忆，写入 memory_items 或提示用户确认。
```

---

## 十四、Memory 设计重点

这是项目第一阶段的重点。

### 14.1 记忆类型

建议 `memory_type` 使用以下枚举或约定字符串：

```text
diet_preference       饮食偏好
food_dislike          不喜欢的食物
allergy_intolerance   过敏 / 不耐受
goal                  长期目标
budget                预算偏好
location              常用位置
scenario              常见饮食场景
sleep                 睡眠相关
body_response         身体反应
restriction           现实限制
habit                 饮食习惯
other                 其他
```

---

### 14.2 哪些内容写入 memory_items

适合写入：

```text
用户喜欢高蛋白食物。
用户不喜欢太油的饭菜。
用户喝牛奶容易肠胃不适。
用户晚饭吃太辣容易影响睡眠。
用户经常在学校食堂吃饭。
用户外食预算通常控制在 25 元以内。
用户常在西南交大犀浦校区附近吃饭。
用户减脂时不希望饿肚子。
```

不适合直接写入：

```text
用户今天中午吃了牛肉饭。
用户今天喝了一杯可乐。
用户刚刚问了晚饭吃什么。
用户临时说今天不想吃鸡肉。
```

这些应该进入 `chat_messages` 或 `meal_logs`，不要直接进入长期 memory。

---

### 14.3 自动记忆与确认机制

根据重要程度区分：

#### 高重要记忆：需要用户确认

例如：

```text
过敏
不耐受
健康状态
长期目标
明显影响饮食建议的身体反应
长期预算约束
常用位置
```

前端展示 `MemoryConfirmCard`：

```text
我可以记住这条信息，之后给你推荐饮食时会参考：
“你喝牛奶容易肠胃不适。”
[确认记住] [不要记住]
```

用户确认后：

```text
memory_items.status = active
source = chat
confidence_score = 0.9
```

用户拒绝：

```text
不写入 memory_items
或写入 status = inactive，按项目现有风格决定
```

#### 低风险偏好：可以自动记

例如：

```text
用户偏好清淡。
用户最近经常吃食堂。
用户喜欢牛肉类盖饭。
```

但也要避免噪声污染：

1. 一次性表达不要过度记忆；
2. 反复出现再提高 importance_score；
3. 不确定的记忆 confidence_score 要低一些；
4. 不要把临时状态当长期偏好。

---

### 14.4 后置记忆抽取

Agent Loop 后执行 memory extraction。

流程：

```text
1. 读取本轮 user message 和 assistant response。
2. 判断是否包含稳定偏好、目标、过敏、不耐受、预算、常用位置、睡眠影响、现实限制等。
3. 根据重要程度决定：
   - 直接写入 active memory；
   - 创建 pending memory，展示确认卡；
   - 不写入。
4. 检查是否与已有 active memory 冲突。
5. 若冲突：
   - 不物理删除旧记忆；
   - 将旧记忆 status 改为 superseded；
   - 新记忆 status = active。
```

---

### 14.5 Memory 检索

第一阶段不要做向量数据库。

使用结构化查询即可：

```text
WHERE user_id = ?
AND status = 'active'
ORDER BY importance_score DESC, updated_at DESC
LIMIT 10 或 20
```

可以按 intent 过滤 memory_type。

例如：

```text
diet_advice:
  goal, diet_preference, food_dislike, allergy_intolerance, budget, sleep, restriction, habit

meal_log:
  habit, scenario, diet_preference

profile_update:
  goal, budget, restriction

dashboard_query:
  goal, habit, budget
```

每次 memory 被用于生成建议时，可以更新 `last_used_at`。

---

## 十五、Memory Center 页面

第一阶段需要做一个 Memory Center / 记忆中心页面。

功能：

```text
1. 查看当前用户所有 active 记忆；
2. 按 memory_type 分组；
3. 编辑记忆内容；
4. 修改记忆类型；
5. 修改重要程度；
6. 禁用记忆；
7. 查看记忆来源和更新时间；
8. 显示记忆是否自动提取 / 手动添加 / 用户确认。
```

页面建议：

```text
src/pages/MemoryCenter.tsx
```

前端展示：

```text
饮食偏好
- 你偏好高蛋白、少油的外食选择

过敏 / 不耐受
- 你喝牛奶容易肠胃不适

预算
- 你一顿外食预算通常控制在 25 元以内

常用场景
- 你经常在学校食堂或校区附近吃饭
```

删除操作不要物理删除，调用接口将 `status` 改为 `inactive`。

---

## 十六、SSE 流式输出要求

第一阶段要做 SSE。

后端返回事件流，前端逐步展示。

建议事件类型：

```text
intent_detected
agent_step
tool_start
tool_result
memory_recalled
action_pending
message_delta
message_done
memory_pending
memory_saved
error
```

示例：

```text
event: intent_detected
data: {"intent":"diet_advice","confidence":0.86}

event: agent_step
data: {"text":"正在读取你的饮食画像..."}

event: tool_start
data: {"tool":"get_user_profile"}

event: tool_result
data: {"tool":"get_user_profile","summary":"已获取目标、预算和睡眠敏感信息"}

event: memory_recalled
data: {"count":3,"summary":["偏好高蛋白","晚餐不宜太油","预算约25元"]}

event: message_delta
data: {"delta":"今晚建议你优先选择..."}

event: message_done
data: {"message_id":123}
```

要求：

1. 前端要能显示最终回复；
2. 前端要能显示简化版执行过程；
3. SSE 出错时要有兜底提示；
4. 不要把模型原始 chain-of-thought 暴露给用户，只展示简化过程。

---

## 十七、Chat 上下文构建要求

AI 生成建议时，不能只看当前一句话。

需要聚合：

```text
1. user_food_profiles：基础画像；
2. memory_items：active 且相关的长期记忆；
3. meal_logs：今日已记录饮食；
4. chat_messages：当前 session 最近若干轮；
5. 当前 intent；
6. 当前用户输入。
```

Prompt 中要明确：

```text
你是一个外食健康饮食助手。
你的目标不是给出医学诊断，而是帮助用户在外食、食堂、快餐、餐馆、外卖场景中做更健康、更可执行的选择。
如果涉及热量、蛋白质等数值，请说明是估算。
如果用户有过敏、不耐受、睡眠敏感等记忆，必须优先考虑。
回答要具体，不要空泛。
尽量给出 2~3 个可执行选项。
```

---

## 十八、餐馆搜索 / 外卖搜索二阶段 TODO

第一阶段不实现百度地图 MCP 和外卖 MCP，但请创建一个待做文档，例如：

```text
docs/TODO_restaurant_takeout_mcp.md
```

内容包括：

```text
二阶段目标：
1. 支持用户手动输入位置，例如“我在西南交大犀浦校区附近”。
2. 将常用位置保存为 memory_items，memory_type = location，重要位置需要用户确认。
3. Agent Loop 内部调用百度地图 MCP，根据位置关键词搜索附近餐馆。
4. 如果未来找到美团 / 外卖商家搜索 MCP，可以增加 takeout_search intent。
5. 餐馆搜索结果不单独建表，优先保存到 chat_messages.action_data。
6. Agent 根据用户记忆筛选餐馆：
   - 减脂 / 增肌目标；
   - 预算；
   - 是否睡眠敏感；
   - 过敏 / 不耐受；
   - 偏好菜系；
   - 距离。
7. 前端展示餐馆候选卡片。
```

第一阶段如果用户问“附近有什么适合减脂的餐馆”，可以先回复：

```text
餐馆搜索能力会在下一阶段接入地图工具。目前你可以告诉我你附近的几个餐馆或外卖选项，我可以先帮你判断哪个更适合你的目标。
```

---

## 十九、代码组织要求

请保持代码清晰，不要乱堆文件。

要求：

1. 不要把所有逻辑写在一个页面或一个 service 中；
2. 前端组件按 chat / memory / profile 分类；
3. 后端按 controller / service / repository / tools / agent / dto 分类；
4. SQL migration 单独放；
5. Prompt 模板可以单独放；
6. 关键业务代码要写必要注释；
7. 注释解释“为什么这样设计”，不要只翻译代码；
8. 保留现有功能，不要破坏 Dashboard、Profile、已有 API；
9. 新增功能要尽量兼容当前数据结构；
10. 如果必须改动已有接口，先说明原因，并尽量保持向后兼容。

建议目录，具体按当前项目技术栈调整：

```text
backend/
  agent/
    DietAgentLoop
    IntentClassifier
    MemoryExtractor
    PromptBuilder
  tools/
    ProfileTools
    MemoryTools
    MealTools
    ChatTools
    DashboardTools
  dto/
    ChatDtos
    IntentDtos
    MemoryDtos
    ActionDtos
  service/
    ChatSessionService
    MemoryService
    MealLogService
    ProfileService
  controller/
    ChatController
    MemoryController

frontend/
  src/components/chat/
  src/components/memory/
  src/pages/Advice.tsx
  src/pages/MemoryCenter.tsx
  src/api/
  src/types/
```

---

## 二十、确认卡 Action 设计

所有重要写操作都不要静默执行。

### 20.1 餐食记录确认卡

```json
{
  "action_type": "meal_log",
  "action_status": "pending",
  "action_data": {
    "food_text": "牛肉饭",
    "meal_type": "lunch",
    "estimated_calories": 650,
    "estimated_protein": 28,
    "estimated_carbs": 85,
    "estimated_fat": 22,
    "calorie_confidence": 0.65,
    "nutrition_source": "llm_estimate"
  }
}
```

### 20.2 基础资料更新确认卡

```json
{
  "action_type": "profile_update",
  "action_status": "pending",
  "action_data": {
    "field": "weight_kg",
    "old_value": 60,
    "new_value": 58,
    "display_text": "检测到你想更新体重为 58kg，是否确认？"
  }
}
```

### 20.3 高重要记忆确认卡

```json
{
  "action_type": "memory_confirm",
  "action_status": "pending",
  "action_data": {
    "memory_type": "allergy_intolerance",
    "content": "用户喝牛奶容易肠胃不适",
    "importance_score": 5,
    "confidence_score": 0.9,
    "display_text": "我可以记住：你喝牛奶容易肠胃不适。以后推荐饮食时会避开或减少奶制品。是否确认？"
  }
}
```

---

## 二十一、第一阶段验收标准

完成后请确保：

### 21.1 Chat UI

```text
1. Advice 页面变成聊天界面；
2. 用户消息右侧显示；
3. AI 消息左侧显示；
4. 底部输入框支持 Enter 发送、Shift+Enter 换行；
5. 新消息自动滚动到底部；
6. 页面顶部有轻量上下文栏。
```

### 21.2 SSE

```text
1. 用户发送消息后能看到流式输出；
2. 能看到“正在读取画像 / 正在召回记忆 / 正在生成建议”等 Agent 过程；
3. 最终回复能够保存到 chat_messages；
4. 刷新后能恢复当前 session 消息。
```

### 21.3 意图识别

```text
1. “我刚吃了牛肉饭” → meal_log；
2. “晚上吃什么比较好” → diet_advice；
3. “我现在体重 58kg” → profile_update；
4. “我喝牛奶容易拉肚子” → memory_candidate；
5. “今天吃了多少热量” → dashboard_query；
6. 普通聊天 → general_chat。
```

### 21.4 餐食记录

```text
1. 识别餐食后出现 MealLogConfirmCard；
2. 用户确认后写入 meal_logs；
3. meal_logs 中包含 calorie_confidence 和 nutrition_source；
4. Dashboard / ChatContextBar 能看到更新。
```

### 21.5 Profile 更新

```text
1. 用户通过聊天说“我现在体重 58kg”；
2. 出现 ProfileUpdateConfirmCard；
3. 用户确认后更新 user_food_profiles；
4. 取消则不更新。
```

### 21.6 Memory

```text
1. 能自动抽取低风险偏好；
2. 高重要记忆出现确认卡；
3. memory_items 支持 status；
4. Memory Center 能查看、编辑、禁用记忆；
5. 禁用记忆后不会再被召回；
6. 冲突记忆不要物理删除，要标记为 superseded。
```

### 21.7 代码质量

```text
1. 文件分类清晰；
2. 关键逻辑有注释；
3. 不破坏现有 Dashboard 和 Profile；
4. 不引入向量数据库；
5. 不实现地图 MCP，只写二阶段 TODO；
6. 不把所有逻辑堆在 Advice.tsx。
```

---

## 二十二、最终开发顺序建议

请按这个顺序做，避免一次性改乱：

```text
Step 1：阅读项目结构，确认当前前后端技术栈和 API。
Step 2：新增 SQL migration：chat_messages、memory_items 增强、meal_logs 增强。
Step 3：补齐后端 chat message / session API。
Step 4：实现 IntentClassifier：规则优先 + LLM 兜底。
Step 5：实现后端 tools：profile、memory、meal、dashboard、chat。
Step 6：实现 SSE chat endpoint。
Step 7：改造 Advice 页面为 Chat UI。
Step 8：实现 MealLogConfirmCard。
Step 9：实现 ProfileUpdateConfirmCard。
Step 10：实现后置 MemoryExtractor。
Step 11：实现 MemoryConfirmCard。
Step 12：实现 Memory Center 页面。
Step 13：创建 docs/TODO_restaurant_takeout_mcp.md。
Step 14：完整测试并修复。
```

---

## 二十三、请先输出计划再动手

在修改代码前，请先输出：

```text
1. 你识别到的当前项目技术栈；
2. 当前已有页面、API、数据库表；
3. 你准备新增 / 修改的文件清单；
4. 你准备新增的 SQL migration；
5. 你对第一阶段范围的理解；
6. 可能存在的风险点。
```

确认计划合理后，再开始改代码。

---

## 二十四、核心原则

请始终遵守：

```text
不推倒重来。
不一次性做太大。
优先完成聊天主入口。
优先完成 memory 能力。
写操作要确认。
低风险偏好可自动记忆。
高重要记忆要用户确认。
餐食记录要用户确认。
AI 估算要标注估算值。
第一阶段不做向量数据库。
第一阶段不做地图 MCP。
代码文件分类清晰。
保留 Dashboard 和 Profile。
```
