import { useEffect, useState, useRef } from 'react';
import { AgentStep } from '../../types';

/**
 * 思考过程气泡
 * ----------------
 * - 在 ChatMessageList 里嵌在 assistant 消息气泡内部使用。
 * - streaming=true 时默认展开并保持"正在思考"动画；
 * - streaming=false 时默认折叠成"查看思考过程 (N步)"，用户可点开回顾。
 *
 * 之所以拆掉原来的底部面板：
 *   1) 思考过程属于"即将到来"的那条 assistant 消息，跟着消息走才符合预期。
 *   2) 历史消息里也能继续保留这份 trace，让用户随时回看当时的推理路径。
 */
interface ThinkingBubbleProps {
  steps: AgentStep[];
  isStreaming: boolean;
  // 受控展开状态（来自父组件记忆用户偏好）；不传则走内部 state。
  expanded?: boolean;
  onToggle?: () => void;
  theme?: 'light' | 'dark';
}

// 步骤的展示标签。后端 AgentStep 枚举见 backend/app/agent/diet_agent_loop.py。
// 这里只做映射，不引入新概念。
const stepLabels: Record<string, string> = {
  intent_detected: '意图识别',
  loading_profile: '读取画像',
  loading_memories: '召回记忆',
  loading_today_meals: '查看今日餐食',
  loading_recent_chat: '查看最近对话',
  parsing_meal: '解析餐食',
  parsing_profile_update: '解析资料更新',
  creating_pending_action: '创建确认卡',
  generating_advice: '生成建议',
  extracting_memories: '抽取记忆',
  memory_saved: '已记住',
  final_response: '完成',
  // ReAct loop steps
  react_call_llm: 'LLM 思考',
  react_tool_call: '调用工具',
  react_tool_result: '工具返回',
  react_tool_error: '工具异常',
  react_direct_response: '直接回答',
  react_max_iterations: '达到轮次上限',
  react_hint_progress: '提示：换关键词',
  react_hint_tool_reminder: '提示：可调用工具',
  react_hint_near_limit: '提示：快到上限',
  react_hint_stuck: '提示：建议直接回答',
};

const stepIcons: Record<string, string> = {
  intent_detected: '🎯',
  loading_profile: '👤',
  loading_memories: '🧠',
  loading_today_meals: '🍽️',
  loading_recent_chat: '💬',
  parsing_meal: '📝',
  parsing_profile_update: '📋',
  creating_pending_action: '✨',
  generating_advice: '💡',
  extracting_memories: '💾',
  memory_saved: '✅',
  final_response: '🏁',
  // ReAct loop
  react_call_llm: '🤖',
  react_tool_call: '🔧',
  react_tool_result: '📥',
  react_tool_error: '⚠️',
  react_direct_response: '💬',
  react_max_iterations: '⏳',
  react_hint_progress: '🔁',
  react_hint_tool_reminder: '🔔',
  react_hint_near_limit: '⚡',
  react_hint_stuck: '🌀',
};

// 视觉分组：把 4 个 DB 加载步骤并成一行"准备上下文"，
// 避免对用户暴露 pipeline 内部细节。
const PREPARATION_STEPS = new Set([
  'loading_profile',
  'loading_memories',
  'loading_today_meals',
  'loading_recent_chat',
]);

const stepColors: Record<string, string> = {
  intent_detected: 'text-blue-400',
  // preparation group
  loading_profile: 'text-gray-400',
  loading_memories: 'text-gray-400',
  loading_today_meals: 'text-gray-400',
  loading_recent_chat: 'text-gray-400',
  // intent-specific
  parsing_meal: 'text-cyan-400',
  parsing_profile_update: 'text-pink-400',
  creating_pending_action: 'text-orange-400',
  generating_advice: 'text-indigo-400',
  // memory
  extracting_memories: 'text-teal-400',
  memory_saved: 'text-emerald-400',
  final_response: 'text-emerald-400',
  // ReAct
  react_call_llm: 'text-violet-400',
  react_tool_call: 'text-blue-400',
  react_tool_result: 'text-cyan-400',
  react_tool_error: 'text-red-400',
  react_direct_response: 'text-emerald-400',
  react_max_iterations: 'text-amber-400',
  react_hint_progress: 'text-gray-400',
  react_hint_tool_reminder: 'text-yellow-400',
  react_hint_near_limit: 'text-orange-400',
  react_hint_stuck: 'text-rose-400',
};

interface GroupedStep {
  key: string;
  label: string;
  icon: string;
  color: string;
  meta?: string; // 右侧辅助说明，例如 "3条" / "general_chat" / "第1轮"
  step: string; // 用于点击 / 调试的原始 key
}

/**
 * 把连续的 PREPARATION_STEPS 折叠成单条"准备上下文"行，
 * 其它步骤保持原样。
 */
function groupSteps(steps: AgentStep[]): GroupedStep[] {
  const out: GroupedStep[] = [];
  let prepBuffer: AgentStep[] = [];

  const flushPrep = () => {
    if (prepBuffer.length === 0) return;
    out.push({
      key: `prep-${prepBuffer[0].timestamp}`,
      label: '准备上下文',
      icon: '🧰',
      color: 'text-gray-400',
      step: 'preparation',
    });
    prepBuffer = [];
  };

  for (const s of steps) {
    if (PREPARATION_STEPS.has(s.step)) {
      prepBuffer.push(s);
      continue;
    }
    flushPrep();
    const meta = describeStepData(s);
    out.push({
      key: `${s.timestamp}-${s.step}`,
      label: stepLabels[s.step] || s.step,
      icon: stepIcons[s.step] || '•',
      color: stepColors[s.step] || 'text-gray-400',
      meta,
      step: s.step,
    });
  }
  flushPrep();
  return out;
}

function describeStepData(s: AgentStep): string | undefined {
  const d = s.data || {};
  if (s.step === 'intent_detected') {
    if (d.primary_intent) {
      const map: Record<string, string> = {
        meal_log: '记录饮食',
        profile_update: '更新资料',
        memory_candidate: '长期记忆',
        dashboard_query: '查看今日',
        restaurant_search_planned: '查找餐厅',
        general_chat: '日常聊天',
      };
      return map[d.primary_intent] || d.primary_intent;
    }
  }
  if (s.step === 'loading_memories' && typeof d.count === 'number') {
    return `${d.count} 条`;
  }
  if (s.step === 'loading_today_meals' && typeof d.meal_count === 'number') {
    return `${d.meal_count} 餐`;
  }
  if (s.step === 'loading_recent_chat' && typeof d.count === 'number') {
    return `${d.count} 条`;
  }
  if (s.step === 'creating_pending_action' && d.action_type) {
    const map: Record<string, string> = {
      meal_log: '记录饮食',
      profile_update: '更新资料',
      restaurant_search: '选择餐厅',
    };
    return map[d.action_type] || d.action_type;
  }
  if (s.step === 'react_call_llm' && typeof d.iteration === 'number') {
    return `第 ${d.iteration} 轮`;
  }
  if (s.step === 'react_tool_call' && d.tool_name) {
    return d.tool_name;
  }
  if (s.step === 'memory_saved' && d.memory_type) {
    return d.memory_type;
  }
  return undefined;
}

export default function ThinkingBubble({
  steps,
  isStreaming,
  expanded: controlledExpanded,
  onToggle,
  theme = 'dark',
}: ThinkingBubbleProps) {
  const isDark = theme === 'dark';
  const [internalExpanded, setInternalExpanded] = useState(isStreaming);
  const isControlled = controlledExpanded !== undefined;
  const expanded = isControlled ? controlledExpanded : internalExpanded;

  // 关键：流式结束时把展开态折叠回去，
  // 这样历史消息默认收起，避免长 trace 占屏。
  const prevStreamingRef = useRef(isStreaming);
  useEffect(() => {
    if (prevStreamingRef.current && !isStreaming) {
      if (!isControlled) setInternalExpanded(false);
    }
    prevStreamingRef.current = isStreaming;
  }, [isStreaming, isControlled]);

  // 没有任何步骤：streaming 时显示"正在思考"，否则不渲染
  if (steps.length === 0) {
    if (!isStreaming) return null;
    return (
      <div
        className={`flex items-center gap-2 text-xs ${
          isDark ? 'text-gray-400' : 'text-gray-500'
        }`}
      >
        <span className="inline-flex gap-0.5">
          <span
            className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
            style={{ animationDelay: '120ms' }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
            style={{ animationDelay: '240ms' }}
          />
        </span>
        <span>正在思考…</span>
      </div>
    );
  }

  const grouped = groupSteps(steps);
  const latest = grouped[grouped.length - 1];

  const handleToggle = () => {
    if (onToggle) onToggle();
    if (!isControlled) setInternalExpanded((v) => !v);
  };

  // 折叠态：展示一行"⚡ 查看思考过程 (N步) · 最新：xxx"
  if (!expanded) {
    return (
      <button
        type="button"
        onClick={handleToggle}
        className={`group flex items-center gap-2 text-xs transition-colors ${
          isDark
            ? 'text-gray-500 hover:text-gray-300'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        <span>⚡</span>
        <span>查看思考过程</span>
        <span
          className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
            isDark
              ? 'bg-gray-700/60 text-gray-300'
              : 'bg-gray-200 text-gray-600'
          }`}
        >
          {grouped.length} 步
        </span>
        {latest && (
          <span
            className={`hidden sm:inline-flex items-center gap-1 truncate max-w-[180px] ${
              isDark ? 'text-gray-500' : 'text-gray-400'
            }`}
          >
            <span className="opacity-70">·</span>
            <span>{latest.icon}</span>
            <span className="truncate">{latest.label}</span>
          </span>
        )}
        <svg
          className="w-3 h-3 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
    );
  }

  // 展开态
  return (
    <div
      className={`rounded-lg border ${
        isDark
          ? 'border-gray-700/60 bg-gray-900/40'
          : 'border-gray-200 bg-gray-50'
      } overflow-hidden`}
    >
      <button
        type="button"
        onClick={handleToggle}
        className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium transition-colors ${
          isDark
            ? 'text-gray-300 hover:bg-gray-800/60'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
      >
        <div className="flex items-center gap-2">
          <span>⚡</span>
          <span>{isStreaming ? 'AI 正在思考' : '思考过程'}</span>
          <span
            className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              isDark
                ? 'bg-primary-500/15 text-primary-300'
                : 'bg-primary-50 text-primary-600'
            }`}
          >
            {grouped.length} 步
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <span
              className={`inline-flex gap-0.5 ${
                isDark ? 'text-primary-300' : 'text-primary-500'
              }`}
            >
              <span
                className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
                style={{ animationDelay: '0ms' }}
              />
              <span
                className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
                style={{ animationDelay: '120ms' }}
              />
              <span
                className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
                style={{ animationDelay: '240ms' }}
              />
            </span>
          )}
          <svg
            className="w-3 h-3 transition-transform rotate-180"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      <ol
        className={`px-3 py-2 space-y-1 text-xs border-t ${
          isDark ? 'border-gray-700/60' : 'border-gray-200'
        }`}
      >
        {grouped.map((g, i) => {
          const isLatest = i === grouped.length - 1;
          return (
            <li
              key={g.key}
              className={`flex items-center gap-2 ${
                isLatest && isStreaming
                  ? isDark
                    ? 'text-gray-100'
                    : 'text-gray-900'
                  : isDark
                    ? 'text-gray-400'
                    : 'text-gray-600'
              }`}
            >
              <span
                className={`flex-shrink-0 w-4 text-center ${
                  isLatest && isStreaming ? 'animate-pulse' : 'opacity-70'
                }`}
              >
                {g.icon}
              </span>
              <span
                className={`flex-shrink-0 tabular-nums opacity-60 ${
                  isLatest && isStreaming ? 'opacity-100' : ''
                }`}
              >
                {i + 1}.
              </span>
              <span
                className={`truncate ${g.color} ${
                  isLatest && isStreaming ? 'font-medium' : ''
                }`}
              >
                {g.label}
              </span>
              {g.meta && (
                <span
                  className={`ml-auto text-[10px] truncate max-w-[140px] ${
                    isDark ? 'text-gray-500' : 'text-gray-400'
                  }`}
                >
                  {g.meta}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
