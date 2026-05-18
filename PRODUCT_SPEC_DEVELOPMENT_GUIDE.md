你现在是一个资深全栈工程师 + AI Agent 产品经理，请你从 0 开始帮我开发一个 ToC 产品。

产品名称暂定：EatFit AI  
中文名：外食健康饮食 Agent / 外食增肌减脂助手

---

# 一、产品定位

这是一个面向普通学生、上班族、健身人群的外食健康饮食 Agent。

它不是医疗诊断工具，不是减肥药推荐工具，也不是传统卡路里记录 App。

它的核心作用是：

用户经常在外吃饭、点外卖、吃食堂、便利店买饭，但又想：

1. 减脂
2. 增肌
3. 控糖
4. 少油少盐
5. 改善睡眠
6. 不想复杂计算热量
7. 不知道每顿具体该怎么选

用户可以告诉 Agent：

- 自己的身高、体重、体脂率
- 当前目标
- 饮食习惯
- 运动频率
- 睡眠情况
- 今天吃了什么
- 附近能吃什么
- 想点什么外卖
- 某家店菜单截图或文字
- 今天是否训练
- 晚上怕不怕影响睡眠

Agent 作为“外食健康饮食助手”，帮助用户：

1. 推荐当前这一顿怎么吃
2. 分析某顿饭是否适合减脂 / 增肌 / 睡眠
3. 帮用户在外卖、食堂、便利店场景中做选择
4. 估算大致热量、蛋白质、碳水、脂肪
5. 给出更健康的点餐修改建议
6. 记录用户饮食和偏好
7. 长期记住用户的目标、口味、忌口、训练习惯、睡眠触发因素
8. 每周生成饮食复盘和下周策略

产品目标不是让用户精确称重，而是让普通人“吃得更可执行、更健康、更适合自己的目标”。

---

# 二、重要安全边界

这个产品必须是“健康、温和、可持续的饮食建议助手”，不能变成极端减肥工具。

必须遵守以下原则：

1. 不提供极端节食建议
2. 不鼓励长期低热量、断食、催吐、滥用泻药、减肥药
3. 不提供医疗诊断，不替代医生、营养师
4. 如果用户提到糖尿病、肾病、肝病、胃病、进食障碍、严重失眠、孕期等情况，应建议咨询医生或专业营养师
5. 不根据单次饮食制造焦虑，不羞辱用户
6. 不使用“你胖”“你自律差”等攻击性文案
7. 给出的建议要可执行，不要空泛地只说“少吃多动”
8. 强调长期习惯、稳定执行、渐进改善
9. 对热量和营养估算必须说明是粗略估算
10. 不承诺“几天瘦多少斤”“必瘦”“快速暴瘦”

产品文案强调：

- 外食也可以吃得更健康
- 不用精确称重，也能做出更好的选择
- 不制造焦虑，只帮你多做一个更优选择
- 增肌减脂靠长期习惯，不靠极端节食

---

# 三、目标用户

主要用户是：

1. 没厨房、住学校宿舍的学生
2. 经常点外卖的上班族
3. 想减脂但不知道每顿吃什么的人
4. 想增肌但蛋白质经常吃不够的人
5. 晚上睡眠差，担心晚餐影响睡眠的人
6. 健身新手，不懂怎么安排训练日和休息日饮食的人
7. 不想复杂记卡路里，但想要方向正确的人
8. 经常在食堂、便利店、快餐店吃饭的人
9. 想少糖、少油、少盐，但不知道怎么点餐的人

---

# 四、MVP 核心功能

先做一个能跑通、能演示、后续方便扩展付费功能的 MVP。

本版本先不做会员、不做付费、不做额度限制。

MVP 必须包含：

---

## 1. 用户注册 / 登录

- 支持注册、登录、退出
- 使用 JWT
- 密码加密保存
- 用户数据保存到 MySQL 数据库
- 登录后进入 Dashboard
- 用户可以编辑自己的健康饮食画像

---

## 2. 首页 Landing Page

页面要像一个 ToC AI SaaS 产品。

文案重点：

- “不知道今天中午吃什么？”
- “想减脂，但外卖越点越乱？”
- “训练后不知道怎么补蛋白？”
- “晚上怕吃太油影响睡眠？”
- “让 EatFit AI 帮你在外食场景中做更好的选择。”

强调：

- 外食也能增肌减脂
- 不用复杂算卡路里
- 根据你的目标、口味、训练和睡眠情况推荐
- 每次选择都比昨天更好一点

---

## 3. Dashboard 仪表盘

展示：

- 用户昵称
- 当前目标：减脂 / 增肌 / 维持 / 控糖 / 改善睡眠
- 今日饮食记录
- 今日蛋白质估算
- 今日热量估算
- 最近体重记录
- 最近训练记录
- 最近饮食建议记录
- 重要长期记忆

快捷入口：

- 今天吃什么？
- 记录一餐
- 分析这顿饭
- 生成一周复盘
- 管理我的记忆

---

## 4. 用户健康饮食画像 User Food Profile

每个用户有一个长期画像。

字段包括：

- nickname：用户昵称
- gender：性别，可选
- age：年龄，可选
- height_cm：身高 cm，可选
- weight_kg：体重 kg，可选
- body_fat_percent：体脂率，可选
- target_weight_kg：目标体重，可选
- primary_goal：主要目标
  - FAT_LOSS 减脂
  - MUSCLE_GAIN 增肌
  - MAINTAIN 维持
  - SLEEP_FRIENDLY 改善睡眠
  - LOW_SUGAR 控糖
  - GENERAL_HEALTH 普通健康
- activity_level：活动水平
  - SEDENTARY 久坐
  - LIGHT 轻度活动
  - MODERATE 中等活动
  - ACTIVE 高活动
- training_frequency：每周训练次数
- training_type：力量训练 / 跑步 / 球类 / 无固定训练 / 其他
- food_preferences：喜欢吃什么
- food_dislikes：不喜欢吃什么
- allergies：过敏或忌口
- budget_per_meal：每餐预算
- common_eating_scenarios：常见场景
  - 食堂
  - 外卖
  - 便利店
  - 快餐
  - 粉面
  - 盖饭
  - 轻食
  - 火锅 / 串串
- sleep_sensitive：是否容易被饮食影响睡眠
- sleep_notes：睡眠相关说明
- notes：补充说明

---

## 5. 外食饮食咨询 Chat / Advice

用户可以输入：

- 当前问题
- 今天什么时候吃
- 是否训练日
- 想吃什么
- 有哪些可选餐厅 / 菜品
- 粘贴外卖菜单
- 粘贴今天已经吃过的东西
- 自己担心的问题，例如“怕胖”“怕睡不着”“蛋白质不够”

Agent 需要输出结构化建议：

- 当前情况判断
- 这一餐的推荐策略
- 推荐选项，至少 3 个
- 每个选项说明：
  - 为什么适合
  - 大致热量估算
  - 蛋白质估算
  - 碳水估算
  - 脂肪估算
  - 适合目标
  - 点餐修改建议
- 不推荐选项
- 如果已经吃了，给出补救建议
- 如果是晚餐，给出睡眠友好提醒
- 如果是训练后，给出蛋白质补充建议
- 今天剩余饮食建议
- 风险提醒
- 一句话总结

输出要具体，不要空泛。

错误示例：

> 多吃蛋白质，少吃油。

正确示例：

> 可以选牛肉饭，但建议米饭半份、加一份青菜、不要额外浇汁；如果训练后吃，可以加一个鸡蛋或一盒牛奶。

---

## 6. 饮食记录 Meal Log

用户可以记录每天吃了什么。

支持：

- 早餐
- 午餐
- 晚餐
- 加餐
- 训练后补充
- 夜宵

字段包括：

- meal_type：早餐 / 午餐 / 晚餐 / 加餐 / 夜宵
- meal_time
- food_text：用户输入的食物描述
- scenario：食堂 / 外卖 / 便利店 / 自己做 / 聚餐 / 其他
- estimated_calories
- estimated_protein
- estimated_carbs
- estimated_fat
- health_score：1-10
- sleep_impact：LOW / MEDIUM / HIGH / UNKNOWN
- ai_comment
- created_at

---

## 7. 个性化长期记忆

这是产品核心差异化。

Agent 需要记住：

- 用户主要目标
- 用户长期体重变化
- 用户体脂率变化
- 用户训练习惯
- 用户喜欢吃什么
- 用户不喜欢吃什么
- 用户常吃的外卖 / 食堂类型
- 用户预算
- 用户容易失控的场景
- 用户晚上吃什么会影响睡眠
- 用户能长期执行的饮食方式
- 哪些建议用户接受过
- 哪些建议用户不喜欢
- 用户常见问题，例如蛋白质不足、晚餐太油、下午喝含糖饮料

记忆分成：

- USER_PROFILE：用户基础画像
- DIET_PREFERENCE：饮食偏好
- FOOD_DISLIKE：不喜欢或忌口
- ROUTINE：作息和训练习惯
- SLEEP_TRIGGER：影响睡眠的饮食因素
- BEHAVIOR_PATTERN：饮食行为模式
- PROGRESS：阶段性进展
- WARNING：风险提醒
- STRATEGY：有效策略

每次咨询结束后，系统调用 MemoryExtractor，从用户输入和 Agent 回复中提取 0-3 条值得长期保存的记忆。

不是所有内容都保存，避免垃圾记忆。

例如用户说：

> 我晚上喝可乐经常睡不着。

可以保存：

```json
{
  "memoryType": "SLEEP_TRIGGER",
  "content": "用户晚上喝可乐后容易入睡困难，晚餐和夜间建议避免含咖啡因饮料。",
  "importanceScore": 9,
  "source": "auto_extracted"
}
```

例如用户说：

> 我不太喜欢轻食，感觉吃不饱，更能接受牛肉饭、鸡腿饭。

可以保存：

```json
{
  "memoryType": "DIET_PREFERENCE",
  "content": "用户不喜欢太清淡的轻食，更能接受牛肉饭、鸡腿饭等有饱腹感的外食选择。",
  "importanceScore": 8,
  "source": "auto_extracted"
}
```

---

## 8. 记忆管理页面

用户可以：

- 查看 Agent 记住了什么
- 按记忆类型筛选
- 删除某条记忆
- 清空全部记忆
- 关闭自动记忆
- 手动添加一条记忆
- 编辑已有记忆

---

## 9. 每日饮食建议

用户可以点击“今天怎么吃”。

Agent 根据：

- 用户画像
- 长期记忆
- 今天是否训练
- 当前时间
- 今天已记录饮食
- 用户目标
- 睡眠敏感程度

生成：

- 早餐建议
- 午餐建议
- 晚餐建议
- 加餐建议
- 今日蛋白质重点
- 今日避坑提醒
- 睡眠友好提醒

---

## 10. 一周饮食复盘

对用户最近 7 天生成报告：

- 本周整体总结
- 做得好的地方
- 主要问题
- 蛋白质是否稳定
- 晚餐是否影响睡眠
- 外食选择是否越来越健康
- 体重 / 体脂率记录变化
- 下周建议
- 下周 3 条可执行策略

---

# 五、MCP 设计要求

这个项目需要体现 MCP / Tool Calling 思想。

MVP 阶段可以先实现“类 MCP 工具层”，不要求一开始就接入真实外部 MCP 服务器，但代码结构要方便后续改造成 MCP Server。

请实现以下工具服务，命名上体现 MCP-ready。

---

## 1. memory_tool

功能：

- search_memories(user_id, query, memory_types)
- upsert_memory(user_id, memory_type, content, importance_score, source)
- delete_memory(memory_id)
- list_memories(user_id)
- update_memory(memory_id)

---

## 2. nutrition_tool

功能：

- estimate_meal_nutrition(food_text)
- compare_food_options(options, user_goal)
- score_meal_for_goal(food_text, goal)
- suggest_healthier_modification(food_text)

MVP 可以使用规则 + Mock 数据估算，不需要真实营养数据库。

例如：

- 鸡胸肉、牛肉、鸡蛋、牛奶、鱼虾：蛋白质较高
- 炸鸡、奶茶、肥肉、油炸食品：脂肪 / 糖分较高
- 米饭、面条、粉、馒头：碳水较高
- 蔬菜：热量低、纤维高
- 可乐、奶茶：糖分高，晚间可能影响睡眠

---

## 3. meal_log_tool

功能：

- create_meal_log
- list_today_meals
- list_recent_meals
- summarize_daily_intake
- summarize_weekly_intake

---

## 4. profile_tool

功能：

- get_user_food_profile
- update_user_food_profile
- infer_missing_profile_fields

---

## 5. recommendation_tool

功能：

- recommend_meal_options
- generate_daily_plan
- generate_weekly_review

后续可以把这些工具迁移成真正的 MCP Server。

请在 README 中说明：

- 当前实现是 MCP-ready 工具层
- 后续如何拆成独立 MCP Server
- 未来可以接入地图 MCP、外卖菜单 MCP、运动健康 MCP、日历 MCP

---

# 六、技术栈要求

## 后端

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- MySQL 8.x
- pymysql
- JWT Auth
- Passlib / bcrypt 密码加密
- Uvicorn
- httpx 调用 LLM
- python-dotenv

注意：

- 第一版不要使用 Alembic
- 第一版不要生成 migration 文件
- 所有建表 SQL 统一放到 `backend/sql/init.sql`
- 我会手动执行 `init.sql` 初始化数据库

---

## 前端

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

---

## AI 调用

使用 OpenAI-compatible API 设计。

通过环境变量配置：

- LLM_API_KEY
- LLM_BASE_URL
- LLM_MODEL

如果没有配置 API Key，必须使用 MockLLMService，返回固定示例，保证项目本地可运行。

---

## 项目结构建议

```text
eatfit-ai/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      prompts/
      tools/
      utils/
      main.py
    sql/
      init.sql
    requirements.txt
    .env.example
  frontend/
    src/
      api/
      components/
      pages/
      routes/
      types/
      utils/
    package.json
  README.md
  docker-compose.yml
```

---

# 七、数据库要求

数据库使用 MySQL 8.x。

第一版 MVP 不使用 Alembic 自动迁移。

请创建：

```text
backend/sql/init.sql
```

这个文件中写入所有建表语句，由我手动在 MySQL 中执行。

要求：

1. 所有表使用 InnoDB
2. 字符集使用 utf8mb4
3. 排序规则使用 utf8mb4_unicode_ci
4. 主键使用 BIGINT AUTO_INCREMENT
5. 时间字段使用 DATETIME，默认 CURRENT_TIMESTAMP
6. updated_at 使用 ON UPDATE CURRENT_TIMESTAMP
7. 外键要写清楚
8. 需要合理添加索引
9. JSON 类型字段使用 MySQL JSON 类型
10. 不要使用 PostgreSQL 专属语法，例如 JSONB、SERIAL、UUID、TIMESTAMPTZ
11. SQLAlchemy Model 要和 init.sql 中的表结构保持一致
12. README 中要写清楚如何手动执行 init.sql
13. 后端启动时不要自动 drop 表，也不要自动重建表
14. 如果表不存在，提示用户先执行 backend/sql/init.sql
15. 枚举字段优先使用 VARCHAR，不要强依赖数据库 ENUM，方便后续扩展

MySQL 连接配置通过 `.env` 管理：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/eatfit_ai?charset=utf8mb4
```

`.env.example` 中也要给出示例。

请在 `docker-compose.yml` 中提供一个 MySQL 8 服务，方便本地启动：

- 数据库名：eatfit_ai
- 用户名：root
- 密码：123456
- 端口：3306

---

# 八、backend/sql/init.sql 表结构要求

请在 `backend/sql/init.sql` 中至少创建以下表。

---

## 1. users

字段：

- id
- username
- email
- password_hash
- auto_memory_enabled
- created_at
- updated_at

注意：

本版本不做会员、不做付费、不做额度限制。

不要实现：

- plan_type
- monthly_advice_count
- billing
- pricing
- subscription
- payment

---

## 2. user_food_profiles

字段：

- id
- user_id
- nickname
- gender
- age
- height_cm
- weight_kg
- body_fat_percent
- target_weight_kg
- primary_goal
- activity_level
- training_frequency
- training_type
- food_preferences
- food_dislikes
- allergies
- budget_per_meal
- common_eating_scenarios
- sleep_sensitive
- sleep_notes
- notes
- created_at
- updated_at

primary_goal 取值由后端控制：

- FAT_LOSS
- MUSCLE_GAIN
- MAINTAIN
- SLEEP_FRIENDLY
- LOW_SUGAR
- GENERAL_HEALTH

activity_level 取值由后端控制：

- SEDENTARY
- LIGHT
- MODERATE
- ACTIVE

---

## 3. memory_items

字段：

- id
- user_id
- memory_type
- content
- importance_score
- source
- created_at
- updated_at

memory_type 取值由后端控制：

- USER_PROFILE
- DIET_PREFERENCE
- FOOD_DISLIKE
- ROUTINE
- SLEEP_TRIGGER
- BEHAVIOR_PATTERN
- PROGRESS
- WARNING
- STRATEGY

---

## 4. meal_logs

字段：

- id
- user_id
- meal_type
- meal_time
- food_text
- scenario
- estimated_calories
- estimated_protein
- estimated_carbs
- estimated_fat
- health_score
- sleep_impact
- ai_comment
- created_at
- updated_at

meal_type 取值由后端控制：

- BREAKFAST
- LUNCH
- DINNER
- SNACK
- POST_WORKOUT
- NIGHT_SNACK

scenario 取值由后端控制：

- CANTEEN
- TAKEOUT
- CONVENIENCE_STORE
- FAST_FOOD
- RESTAURANT
- HOME_COOKED
- PARTY
- OTHER

sleep_impact 取值由后端控制：

- LOW
- MEDIUM
- HIGH
- UNKNOWN

---

## 5. advice_sessions

字段：

- id
- user_id
- title
- user_question
- context_text
- ai_response_json
- created_at
- updated_at

---

## 6. diet_advice_records

字段：

- id
- user_id
- session_id
- situation_summary
- recommendation_strategy
- recommended_options_json
- not_recommended_json
- estimated_summary_json
- next_meal_advice
- sleep_friendly_tips
- risk_level
- created_at

---

## 7. weight_records

字段：

- id
- user_id
- weight_kg
- record_date
- note
- created_at

---

## 8. body_fat_records

字段：

- id
- user_id
- body_fat_percent
- record_date
- note
- created_at

---

## 9. training_records

字段：

- id
- user_id
- training_type
- duration_minutes
- intensity
- record_date
- note
- created_at

---

# 九、init.sql 必须包含的 SQL

请严格按照以下结构生成 `backend/sql/init.sql`。

```sql
CREATE DATABASE IF NOT EXISTS eatfit_ai
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE eatfit_ai;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  email VARCHAR(128) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  auto_memory_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_food_profiles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  nickname VARCHAR(64),
  gender VARCHAR(32),
  age INT,
  height_cm DECIMAL(5,2),
  weight_kg DECIMAL(5,2),
  body_fat_percent DECIMAL(5,2),
  target_weight_kg DECIMAL(5,2),
  primary_goal VARCHAR(64),
  activity_level VARCHAR(64),
  training_frequency INT,
  training_type VARCHAR(128),
  food_preferences TEXT,
  food_dislikes TEXT,
  allergies TEXT,
  budget_per_meal DECIMAL(8,2),
  common_eating_scenarios TEXT,
  sleep_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
  sleep_notes TEXT,
  notes TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_food_profiles_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_food_profiles_user_id (user_id),
  KEY idx_user_food_profiles_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS memory_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  memory_type VARCHAR(64) NOT NULL,
  content TEXT NOT NULL,
  importance_score INT NOT NULL DEFAULT 5,
  source VARCHAR(64) NOT NULL DEFAULT 'manual',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_memory_items_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_memory_items_user_id (user_id),
  KEY idx_memory_items_memory_type (memory_type),
  KEY idx_memory_items_importance_score (importance_score),
  KEY idx_memory_items_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  meal_type VARCHAR(64) NOT NULL,
  meal_time DATETIME NOT NULL,
  food_text TEXT NOT NULL,
  scenario VARCHAR(64),
  estimated_calories DECIMAL(8,2),
  estimated_protein DECIMAL(8,2),
  estimated_carbs DECIMAL(8,2),
  estimated_fat DECIMAL(8,2),
  health_score INT,
  sleep_impact VARCHAR(64) DEFAULT 'UNKNOWN',
  ai_comment TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_meal_logs_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_meal_logs_user_id (user_id),
  KEY idx_meal_logs_meal_time (meal_time),
  KEY idx_meal_logs_meal_type (meal_type),
  KEY idx_meal_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS advice_sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  title VARCHAR(255),
  user_question TEXT NOT NULL,
  context_text TEXT,
  ai_response_json JSON,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_advice_sessions_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_advice_sessions_user_id (user_id),
  KEY idx_advice_sessions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS diet_advice_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  session_id BIGINT NOT NULL,
  situation_summary TEXT,
  recommendation_strategy TEXT,
  recommended_options_json JSON,
  not_recommended_json JSON,
  estimated_summary_json JSON,
  next_meal_advice TEXT,
  sleep_friendly_tips TEXT,
  risk_level VARCHAR(64) DEFAULT 'LOW',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_diet_advice_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_diet_advice_records_session
    FOREIGN KEY (session_id) REFERENCES advice_sessions(id) ON DELETE CASCADE,
  KEY idx_diet_advice_records_user_id (user_id),
  KEY idx_diet_advice_records_session_id (session_id),
  KEY idx_diet_advice_records_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS weight_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  weight_kg DECIMAL(5,2) NOT NULL,
  record_date DATE NOT NULL,
  note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_weight_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_weight_records_user_id (user_id),
  KEY idx_weight_records_record_date (record_date),
  UNIQUE KEY uk_weight_records_user_date (user_id, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS body_fat_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  body_fat_percent DECIMAL(5,2) NOT NULL,
  record_date DATE NOT NULL,
  note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_body_fat_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_body_fat_records_user_id (user_id),
  KEY idx_body_fat_records_record_date (record_date),
  UNIQUE KEY uk_body_fat_records_user_date (user_id, record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS training_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  training_type VARCHAR(128),
  duration_minutes INT,
  intensity VARCHAR(64),
  record_date DATE NOT NULL,
  note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_training_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  KEY idx_training_records_user_id (user_id),
  KEY idx_training_records_record_date (record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

# 十、后端 API 设计

## Auth

- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout

---

## User Food Profile

- GET /api/profile
- PUT /api/profile
- POST /api/profile/init

---

## Diet Advice

- POST /api/advice/generate
- GET /api/advice/history
- GET /api/advice/history/{id}
- POST /api/advice/daily-plan
- POST /api/advice/weekly-review

---

## Meal Logs

- POST /api/meals
- GET /api/meals/today
- GET /api/meals/recent
- GET /api/meals/{id}
- PUT /api/meals/{id}
- DELETE /api/meals/{id}
- GET /api/meals/summary/daily
- GET /api/meals/summary/weekly

---

## Memory

- GET /api/memories
- POST /api/memories
- PUT /api/memories/{id}
- DELETE /api/memories/{id}
- DELETE /api/memories
- PATCH /api/users/auto-memory

---

## Weight Records

- POST /api/weights
- GET /api/weights
- DELETE /api/weights/{id}

---

## Body Fat Records

- POST /api/body-fat
- GET /api/body-fat
- DELETE /api/body-fat/{id}

---

## Training Records

- POST /api/trainings
- GET /api/trainings
- DELETE /api/trainings/{id}

---

## Health Check

- GET /api/health

---

# 十一、AI Prompt 设计

后端需要实现以下几个 Prompt Builder。

---

## 1. DietAdvicePromptBuilder

输入：

- 用户当前问题
- 用户补充上下文
- 用户健康饮食画像
- 检索到的长期记忆
- 今日饮食记录
- 最近训练记录
- 最近体重记录
- 最近体脂率记录

输出要求：

大模型必须返回 JSON，结构如下：

```json
{
  "situationSummary": "",
  "goalAnalysis": "",
  "recommendationStrategy": "",
  "recommendedOptions": [
    {
      "name": "",
      "whyRecommended": "",
      "estimatedCalories": 0,
      "estimatedProtein": 0,
      "estimatedCarbs": 0,
      "estimatedFat": 0,
      "orderModification": "",
      "suitableFor": [],
      "score": 8
    }
  ],
  "notRecommended": [
    {
      "name": "",
      "reason": "",
      "betterAlternative": ""
    }
  ],
  "todayRemainingAdvice": "",
  "sleepFriendlyTips": "",
  "trainingDayTips": "",
  "nextMealAdvice": "",
  "riskLevel": "LOW",
  "riskWarnings": [],
  "oneSentenceSummary": ""
}
```

Prompt 必须强调：

- 不要提供医疗诊断
- 不要极端节食
- 不要制造身材焦虑
- 热量和营养估算只是粗略估算
- 建议必须具体到“怎么点餐 / 怎么搭配 / 怎么替换”
- 如果用户目标是减脂，也要保证蛋白质和基本营养
- 如果用户晚上容易失眠，晚餐建议避免过辣、过油、大量咖啡因、高糖饮料
- 如果用户是训练日，提醒蛋白质和碳水合理补充
- 如果用户提到疾病、进食障碍、严重睡眠问题，建议寻求专业帮助
- 回复风格要像一个靠谱朋友，不要像医生训话

---

## 2. MemoryExtractorPromptBuilder

输入：

- 用户健康饮食画像
- 用户本轮问题
- AI 本轮建议

输出 JSON：

```json
{
  "memories": [
    {
      "memoryType": "DIET_PREFERENCE",
      "content": "",
      "importanceScore": 8,
      "source": "auto_extracted"
    }
  ]
}
```

要求：

- 只提取长期有价值的信息
- 最多提取 3 条
- 不要保存无意义闲聊
- 不要保存过度敏感、无关隐私
- 不要保存医疗诊断结论
- 不要保存羞辱性标签
- 如果没有值得保存的信息，返回空数组

可以保存的信息类型：

- 用户喜欢的饮食类型
- 用户不喜欢的食物
- 用户常见外食场景
- 用户训练习惯
- 用户睡眠触发因素
- 用户可长期执行的策略
- 用户阶段性目标
- 用户常见饮食问题

---

## 3. DailyPlanPromptBuilder

输入：

- 用户画像
- 长期记忆
- 今日饮食记录
- 今天是否训练
- 当前时间

输出 JSON：

```json
{
  "breakfastSuggestion": "",
  "lunchSuggestion": "",
  "dinnerSuggestion": "",
  "snackSuggestion": "",
  "proteinFocus": "",
  "avoidToday": [],
  "sleepReminder": "",
  "oneDayStrategy": ""
}
```

---

## 4. WeeklyReviewPromptBuilder

输入：

- 用户画像
- 最近 7 天饮食记录
- 最近 7 天训练记录
- 最近体重记录
- 最近体脂率记录
- 长期记忆

输出 JSON：

```json
{
  "weekSummary": "",
  "whatWentWell": [],
  "mainProblems": [],
  "proteinConsistency": "",
  "sleepImpactAnalysis": "",
  "eatingOutPattern": "",
  "weightAndBodyFatTrend": "",
  "nextWeekStrategy": "",
  "nextWeekActions": [],
  "warnings": []
}
```

---

# 十二、前端页面设计

前端至少实现以下页面。

---

## 1. /

Landing Page

展示：

- 产品定位
- 核心功能
- 使用流程
- 用户痛点
- 开始使用按钮

不要展示价格页。  
不要展示会员。  
不要展示 Pro。

---

## 2. /login

登录页。

---

## 3. /register

注册页。

---

## 4. /dashboard

仪表盘。

展示：

- 用户昵称
- 当前目标
- 今日饮食记录
- 今日营养估算
- 最近建议记录
- 重要记忆
- 最近体重记录
- 最近体脂率记录

快捷按钮：

- 今天吃什么
- 记录一餐
- 分析这顿饭
- 一周复盘
- 管理记忆

---

## 5. /profile

用户健康饮食画像页。

支持编辑：

- 身高
- 体重
- 体脂率
- 目标
- 训练频率
- 饮食偏好
- 忌口
- 预算
- 常见饮食场景
- 睡眠敏感情况

---

## 6. /advice

饮食咨询页。

包含：

- 当前问题输入框
- 上下文输入框
- 是否训练日选择
- 当前场景选择：食堂 / 外卖 / 便利店 / 快餐 / 聚餐 / 其他
- 生成建议按钮
- AI 分析结果
- 推荐选项卡片
- 不推荐选项
- 今日剩余建议
- 睡眠友好提醒
- 风险提醒

---

## 7. /meals

饮食记录页。

展示：

- 今日饮食记录
- 新增饮食记录表单
- 每餐估算热量、蛋白质、碳水、脂肪
- AI 点评
- 删除 / 编辑按钮

---

## 8. /memories

记忆管理页。

展示：

- 记忆列表
- 记忆类型
- 重要度
- 来源
- 删除按钮
- 编辑按钮
- 手动添加记忆
- 自动记忆开关

---

## 9. /weekly-review

一周复盘页。

展示：

- 本周总结
- 做得好的地方
- 主要问题
- 下周策略
- 下周行动清单

---

## 10. /progress

进展记录页。

展示：

- 体重记录
- 体脂率记录
- 训练记录
- 新增体重记录
- 新增体脂率记录
- 新增训练记录

---

# 十三、产品体验要求

页面风格：

- 年轻化
- 干净
- 健康
- 轻陪伴感
- 不要像医院系统
- 不要像传统减肥 App
- 不要制造焦虑
- 要像现代 AI SaaS

文案风格：

- 具体
- 温和
- 有执行感
- 不说教
- 不羞辱
- 不承诺快速瘦身
- 强调“多做一个更好的选择”

示例文案：

- “外食也能吃得更适合自己。”
- “不用精确称重，也能把方向吃对。”
- “今天这顿怎么选？让 EatFit AI 帮你分析。”
- “训练后不知道吃什么？先补够蛋白质。”
- “晚上怕睡不好？帮你避开高油、高糖、咖啡因。”
- “不是让你少吃一切，而是帮你吃得更聪明。”

---

# 十四、开发顺序要求

请按以下顺序开发：

第 1 步：检查当前目录，如果为空，创建完整项目结构。

第 2 步：创建 FastAPI 后端项目。

第 3 步：配置 MySQL、SQLAlchemy、数据库连接。

第 4 步：创建 `backend/sql/init.sql`，写入完整 MySQL 建表语句。

第 5 步：实现用户注册登录和 JWT。

第 6 步：实现用户健康饮食画像 User Food Profile。

第 7 步：实现记忆表和记忆管理接口。

第 8 步：实现 Meal Log 饮食记录。

第 9 步：实现 Weight Record、Body Fat Record 和 Training Record。

第 10 步：实现 MCP-ready 工具层：

- memory_tool
- nutrition_tool
- meal_log_tool
- profile_tool
- recommendation_tool

第 11 步：实现 MockLLMService，保证没有 API Key 也能跑。

第 12 步：实现真实 LLMService，支持 OpenAI-compatible API。

第 13 步：实现 DietAdvicePromptBuilder。

第 14 步：实现饮食建议生成接口。

第 15 步：实现 MemoryExtractor 自动记忆。

第 16 步：实现 DailyPlanPromptBuilder 和每日饮食建议接口。

第 17 步：实现 WeeklyReviewPromptBuilder 和一周复盘接口。

第 18 步：实现 React 前端页面。

第 19 步：联调前后端。

第 20 步：写 README。

第 21 步：运行后端和前端构建命令，修复明显报错。

---

# 十五、重要约束

1. 不要做成医疗诊断工具。
2. 不要做成极端减肥工具。
3. 不要做会员 / 付费 / 套餐 / 额度限制。
4. 保留用户注册登录功能。
5. 保留用户画像功能。
6. 保留长期个性化记忆功能。
7. 核心一定是“外食健康饮食建议 + 主动记忆 + 个性化推荐”。
8. 后端必须使用 Python FastAPI。
9. 数据库必须使用 MySQL。
10. 第一版不要使用 Alembic。
11. 第一版不要生成 migration 文件。
12. 所有建表语句必须放在 `backend/sql/init.sql`。
13. 后端启动时不要自动 drop 表，也不要自动重建表。
14. 没有 LLM API Key 时必须能用 MockLLMService 跑通。
15. MVP 单体应用即可，不要过度设计微服务。
16. 所有接口要有清晰的 Pydantic Schema。
17. 所有关键业务代码要有必要注释。
18. 前端先简单好看、能用，不要过度炫技。
19. 不要引入太复杂的组件库，Tailwind 即可。
20. 出现技术取舍时，优先保证可运行。
21. JSON 解析失败时要有 fallback，不能让接口直接崩。
22. 数据库初始化要简单，README 里必须写清楚。
23. 营养估算可以粗略，但必须可解释。
24. 所有 AI 建议都要带安全边界提醒。
25. 最终告诉我如何启动后端、前端、数据库。

---

# 十六、建议的 Mock 示例

如果没有配置 LLM_API_KEY，MockLLMService 至少返回以下类型的示例。

用户问题：

> 我晚上训练完想吃牛肉饭，可以吗？我怕影响睡眠。

Mock 返回：

```json
{
  "situationSummary": "用户是训练后晚餐场景，希望补充蛋白质，同时担心晚餐影响睡眠。",
  "goalAnalysis": "训练后需要补充蛋白质和适量碳水，但晚餐应避免过油、过辣和大量含糖饮料。",
  "recommendationStrategy": "可以吃牛肉饭，但要调整点餐方式：米饭半份或正常份根据饥饿程度选择，少酱汁，加青菜，避免辣油和含糖饮料。",
  "recommendedOptions": [
    {
      "name": "少油牛肉饭 + 青菜 + 无糖饮料",
      "whyRecommended": "牛肉能提供蛋白质，米饭补充训练后糖原，青菜增加饱腹感和纤维。",
      "estimatedCalories": 650,
      "estimatedProtein": 35,
      "estimatedCarbs": 75,
      "estimatedFat": 20,
      "orderModification": "备注少油少酱，米饭半份或七分，额外加青菜，不要辣油。",
      "suitableFor": ["训练后", "增肌减脂", "外食场景"],
      "score": 8
    },
    {
      "name": "鸡腿饭去皮 + 青菜 + 鸡蛋",
      "whyRecommended": "蛋白质更稳定，脂肪可通过去皮和少酱降低。",
      "estimatedCalories": 600,
      "estimatedProtein": 38,
      "estimatedCarbs": 65,
      "estimatedFat": 18,
      "orderModification": "鸡腿尽量去皮，少酱汁，加一份青菜。",
      "suitableFor": ["训练后", "高蛋白"],
      "score": 8
    },
    {
      "name": "牛肉粉少汤 + 加蛋",
      "whyRecommended": "比重油盖饭更清爽，加蛋可以提高蛋白质。",
      "estimatedCalories": 550,
      "estimatedProtein": 30,
      "estimatedCarbs": 70,
      "estimatedFat": 12,
      "orderModification": "少喝汤，少辣，加一个鸡蛋。",
      "suitableFor": ["晚餐", "睡眠友好"],
      "score": 7
    }
  ],
  "notRecommended": [
    {
      "name": "重辣肥牛饭 + 可乐",
      "reason": "油脂、辣度和含糖饮料都可能影响睡眠，也容易让总热量偏高。",
      "betterAlternative": "选择少油牛肉饭，饮料换成水或无糖茶。"
    }
  ],
  "todayRemainingAdvice": "如果这顿吃了牛肉饭，夜里不要再加高糖零食；如果仍然饿，可以选择牛奶或无糖酸奶。",
  "sleepFriendlyTips": "晚餐尽量避免可乐、奶茶、浓茶、咖啡和特别辣的食物。",
  "trainingDayTips": "训练后这顿可以保留适量主食，不建议完全不吃碳水。",
  "nextMealAdvice": "明天早餐可以选择鸡蛋、牛奶、全麦面包或包子搭配无糖豆浆，继续保证蛋白质。",
  "riskLevel": "LOW",
  "riskWarnings": [
    "以上热量和营养为粗略估算，不等同于精确营养计算。",
    "如果有特殊疾病或长期睡眠障碍，请咨询医生或营养师。"
  ],
  "oneSentenceSummary": "可以吃牛肉饭，但关键是少油少酱、加青菜、避开含糖饮料。"
}
```

---

# 十七、README 必须包含

README.md 至少写清楚：

1. 项目介绍
2. 功能列表
3. 技术栈
4. 后端启动方式
5. 前端启动方式
6. MySQL / Docker Compose 启动方式
7. `backend/sql/init.sql` 手动初始化方式
8. `.env.example` 说明
9. MockLLMService 模式
10. OpenAI-compatible API 配置方式
11. MCP-ready 工具层说明
12. 主要 API 列表
13. 项目目录结构
14. 后续迭代方向

---

# 十八、数据库初始化说明必须写进 README

README 中必须包含类似以下说明。

## 1. 启动 MySQL

如果使用 Docker：

```bash
docker compose up -d mysql
```

## 2. 创建数据库并执行初始化 SQL

方式一：命令行执行：

```bash
mysql -uroot -p123456 < backend/sql/init.sql
```

方式二：Navicat 手动执行：

1. 连接本地 MySQL
2. 新建查询
3. 打开 `backend/sql/init.sql`
4. 执行全部 SQL

## 3. 配置后端环境变量

复制环境变量文件：

```bash
cd backend
cp .env.example .env
```

`.env` 示例：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/eatfit_ai?charset=utf8mb4

JWT_SECRET_KEY=please-change-this-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

FRONTEND_ORIGIN=http://localhost:5173
```

## 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

# 十九、最终交付

请你最终交付：

1. 完整可运行代码
2. 后端启动命令
3. 前端启动命令
4. MySQL 数据库初始化方式
5. `backend/sql/init.sql`
6. `.env.example`
7. LLM API Key 配置方式
8. Mock 模式说明
9. 注册登录流程
10. README.md
11. MCP-ready 工具层说明
12. 后续拆成真实 MCP Server 的建议
13. 后续接入地图 / 外卖 / 运动健康数据的建议
14. 后续真实付费功能接入建议，但本版本不要实现
15. 后续产品迭代建议

---

现在请开始开发。