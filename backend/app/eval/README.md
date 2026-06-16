# Memory-Recall Eval

离线评测 MemoryTools 的召回路径。**不依赖 LLM**，跑得快，能进 CI 防回归。

## 跑

```bash
cd backend
PYTHONPATH=. python -m app.eval.runner
```

可选参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--cases` | `app/eval/cases/memory_recall.yaml` | cases 文件 |
| `--user-id N` | cases 里写死的 | 全部 case 用同一个 user_id（sandbox 跑测试数据时用） |
| `--k 3,5,10` | `3,5,10` | 算 Recall/Hit/Type-Precision 的 K |
| `--json` | 关 | 末尾把全量结果 dump 成 JSON |

## 输出

每个 case 一段：
```
── lactose_after_dairy_symptom ──
  query:    刚喝了奶茶，胃有点不舒服
  intent:   diet_advice
  notes:    乳糖不耐受应该被召回
  expected: ids=[6] types=[allergy_intolerance]
  retrieved (top 10):
    #  6 allergy_intolerance  imp=8 sim=0.842 score=0.745 | 乳糖不耐受
    ...
  metrics:  recall@3=1.000  hit@3=1.000  type_precision@3=1.000  recall@5=1.000  ...
```

末尾是全 case 平均。

## 指标定义

| 指标 | 含义 |
|---|---|
| `recall@K` | 期望 id 在 top-K 中出现的比例（None 表示无 ground truth） |
| `hit@K` | top-K 至少有一个期望 id 即 1 |
| `type_precision@K` | top-K 中属于期望 type 的比例（粗粒度，看是否拉到正确类别） |
| `mrr` | 第一个期望 id 出现的位置的倒数；都没出现则 0 |

## 加新 case

编辑 `cases/memory_recall.yaml`，加一条：

```yaml
- case_id: <唯一>
  user_id: <用哪个用户>
  intent: <diet_advice / meal_log / profile_update / dashboard_query>
  query: "<用户原话>"
  relevant_memory_ids: [<期望在 top-K 里的 memory.id>]
  relevant_types: [<期望的 memory_type>]
  notes: "<为什么这个 case 值得测>"
```

要查真实 memory id：

```sql
SELECT id, memory_type, content, importance_score
FROM memory_items WHERE user_id = 1 AND status = 'active' ORDER BY id;
```

## 为什么是这套

- **基于真实 DB**：评测不构造 fake embedding，直接走 Ollama + pgvector，召回路径和生产一致
- **不依赖 LLM**：跑一遍 < 30s，能进 CI
- **side-effect free**：`snapshot.py` 包住 `last_used_at`，跑完 DB 状态完全一致
- **可扩展**：加 case 是 YAML，加指标改 `metrics.py`

## 已知限制

- **覆盖面受真实数据约束**：user 1 现有 7 条 memory，覆盖 3 个 type（allergy / dislike / preference）。goal / budget / location / scenario / sleep / restriction 在当前数据下永远是 0 分。要测这些 type 需要先 seed 数据。
- **不能评估"该不该存"**：只评"该召回的召回了没"。能否抽取 → 写到 memory 是另一个评测维度。
- **embedding 不可控**：Ollama 模型换了 → 指标会变。CI 里要 pin 模型版本。
- **Ollama 不可用时降级到 importance-only**：eval 不会崩，但 `sim/score` 全是 NaN（见下文）。已知 bug 已登记 `发现的bug.md` → BUG-20260615-01。

## 已知 bug 引用

跑这套 eval 暴露了一个生产代码 bug：`MemoryTools._hybrid_search` 在 Ollama 不可用时返回 `similarity=NaN` / `score=NaN` 到 API 响应。详见 `发现的bug.md` → BUG-20260615-01。建议修完后回归这套 case。
