import { useState, useEffect } from 'react';
import { AgentStep } from '../../types';

interface AgentTracePanelProps {
  steps: AgentStep[];
  isOpen: boolean;
  onToggle: () => void;
}

const stepLabels: Record<string, string> = {
  intent_detected: "意图识别",
  loading_profile: "读取画像",
  loading_memories: "召回记忆",
  loading_today_meals: "查看今日餐食",
  parsing_meal: "解析餐食",
  parsing_profile_update: "解析资料更新",
  creating_pending_action: "创建确认卡",
  generating_advice: "生成建议",
  extracting_memories: "抽取记忆",
  memory_saved: "记忆已保存",
  final_response: "最终回复",
  // ReAct loop steps
  react_call_llm: "LLM调用",
  react_tool_call: "工具调用",
  react_tool_result: "工具结果",
  react_tool_error: "工具错误",
  react_direct_response: "直接回复",
  react_max_iterations: "达到上限",
  react_hint_progress: "进度提示",
  react_hint_tool_reminder: "工具提醒",
  react_hint_near_limit: "接近上限",
  react_hint_stuck: "卡住了",
};

const stepIcons: Record<string, string> = {
  intent_detected: "🎯",
  loading_profile: "👤",
  loading_memories: "🧠",
  loading_today_meals: "🍽️",
  parsing_meal: "📝",
  parsing_profile_update: "📋",
  creating_pending_action: "✨",
  generating_advice: "💬",
  extracting_memories: "💾",
  memory_saved: "💾",
  final_response: "✅",
  // ReAct loop steps
  react_call_llm: "🤖",
  react_tool_call: "🔧",
  react_tool_result: "📥",
  react_tool_error: "⚠️",
  react_direct_response: "💡",
  react_max_iterations: "⏳",
  react_hint_progress: "📍",
  react_hint_tool_reminder: "🔔",
  react_hint_near_limit: "⚡",
  react_hint_stuck: "🌀",
};

const stepColors: Record<string, { bg: string; text: string; border: string }> = {
  intent_detected: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  loading_profile: { bg: "bg-green-500/10", text: "text-green-400", border: "border-green-500/30" },
  loading_memories: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30" },
  loading_today_meals: { bg: "bg-yellow-500/10", text: "text-yellow-400", border: "border-yellow-500/30" },
  parsing_meal: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/30" },
  parsing_profile_update: { bg: "bg-pink-500/10", text: "text-pink-400", border: "border-pink-500/30" },
  creating_pending_action: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
  generating_advice: { bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-indigo-500/30" },
  extracting_memories: { bg: "bg-teal-500/10", text: "text-teal-400", border: "border-teal-500/30" },
  memory_saved: { bg: "bg-teal-500/10", text: "text-teal-400", border: "border-teal-500/30" },
  final_response: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  // ReAct loop steps
  react_call_llm: { bg: "bg-violet-500/10", text: "text-violet-400", border: "border-violet-500/30" },
  react_tool_call: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  react_tool_result: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/30" },
  react_tool_error: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
  react_direct_response: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  react_max_iterations: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  react_hint_progress: { bg: "bg-gray-500/10", text: "text-gray-400", border: "border-gray-500/30" },
  react_hint_tool_reminder: { bg: "bg-yellow-500/10", text: "text-yellow-400", border: "border-yellow-500/30" },
  react_hint_near_limit: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
  react_hint_stuck: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/30" },
};

export default function AgentTracePanel({
  steps,
  isOpen,
  onToggle,
}: AgentTracePanelProps) {
  const [visibleSteps, setVisibleSteps] = useState<AgentStep[]>([]);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (steps.length > 0) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 300);
      return () => clearTimeout(timer);
    }
  }, [steps]);

  useEffect(() => {
    if (steps.length > visibleSteps.length) {
      const newSteps = steps.slice(visibleSteps.length);
      newSteps.forEach((step, i) => {
        setTimeout(() => {
          setVisibleSteps(prev => [...prev, step]);
        }, i * 100);
      });
    }
  }, [steps]);

  if (!isOpen && visibleSteps.length === 0) {
    return (
      <button
        onClick={onToggle}
        className="mx-4 mb-2 flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-500/10 border border-primary-500/20 text-primary-400 hover:bg-primary-500/20 transition-all text-sm"
      >
        <span className="text-base">⚡</span>
        <span>查看AI思考过程</span>
      </button>
    );
  }

  return (
    <div className="mx-4 mb-2 rounded-xl bg-gradient-to-r from-primary-500/5 to-transparent border border-primary-500/20 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-primary-500/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="text-lg">⚡</span>
            <span className="text-sm font-medium text-primary-400">AI思考过程</span>
          </div>
          <div className="flex items-center gap-1.5">
            {visibleSteps.length > 0 && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium bg-primary-500/20 text-primary-300 ${isAnimating ? 'animate-pulse' : ''}`}>
                {visibleSteps.length} 步
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isOpen && visibleSteps.length > 0 && (
            <div className="flex gap-1">
              {visibleSteps.slice(-3).map((step, i) => {
                const colors = stepColors[step.step] || { text: "text-gray-400" };
                return (
                  <span key={i} className={`text-sm ${colors.text}`}>
                    {stepIcons[step.step] || '•'}
                  </span>
                );
              })}
            </div>
          )}
          <svg
            className={`w-4 h-4 text-primary-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="px-4 pb-3 space-y-1">
          {visibleSteps.length === 0 ? (
            <div className="py-4 text-center text-sm text-gray-500">正在思考...</div>
          ) : (
            <div className="space-y-1">
              {visibleSteps.map((step, index) => {
                const label = stepLabels[step.step] || step.step;
                const icon = stepIcons[step.step] || '•';
                const colors = stepColors[step.step] || { bg: "bg-gray-500/10", text: "text-gray-400", border: "border-gray-500/20" };

                return (
                  <div
                    key={`${step.timestamp}-${index}`}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg ${colors.bg} border ${colors.border} transition-all duration-200`}
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <span className="text-base">{icon}</span>
                    <span className={`text-sm font-medium ${colors.text}`}>
                      {index + 1}. {label}
                    </span>
                    {step.data.intent && (
                      <span className="ml-auto text-xs text-gray-400 truncate max-w-[120px]">
                        {step.data.intent}
                      </span>
                    )}
                    {step.data.tool_name && (
                      <span className="ml-auto text-xs text-gray-400 truncate max-w-[120px]">
                        {step.data.tool_name}
                      </span>
                    )}
                    {step.data.iteration !== undefined && (
                      <span className="ml-auto text-xs text-gray-500">
                        第{step.data.iteration}轮
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}