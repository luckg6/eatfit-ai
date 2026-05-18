interface MemoryConfirmCardProps {
  memoryAction: {
    memory_type: string;
    content: string;
    importance_score: number;
    confidence_score: number;
    display_text: string;
  };
  onConfirm: () => void;
  onCancel: () => void;
  theme?: 'light' | 'dark';
}

export default function MemoryConfirmCard({
  memoryAction,
  onConfirm,
  onCancel,
  theme = 'dark',
}: MemoryConfirmCardProps) {
  const isDark = theme === 'dark';
  const memoryTypeNames: Record<string, string> = {
    allergy_intolerance: "过敏/不耐受",
    diet_preference: "饮食偏好",
    food_dislike: "不喜欢食物",
    goal: "长期目标",
    budget: "预算偏好",
    location: "常用位置",
    scenario: "饮食场景",
    sleep: "睡眠相关",
    body_response: "身体反应",
    restriction: "现实限制",
    habit: "饮食习惯",
    other: "其他",
  };

  const typeName = memoryTypeNames[memoryAction.memory_type] || memoryAction.memory_type;
  const isHighImportance = ["allergy_intolerance", "body_response", "goal", "restriction"].includes(memoryAction.memory_type);

  return (
    <div className={`ml-10 rounded-lg px-4 py-3 max-w-xs border ${isDark ? 'bg-amber-900/20 border-amber-700/30' : 'bg-amber-50 border-amber-200'}`}>
      <p className={`text-sm font-medium mb-2 ${isDark ? 'text-amber-400' : 'text-amber-600'}`}>
        {isHighImportance ? "🌟 重要记忆" : "💡 记忆建议"}
      </p>
      <div className={`text-sm space-y-2 mb-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
        <p className={isDark ? 'text-gray-500' : 'text-gray-400'}>类型: {typeName}</p>
        <p className="whitespace-pre-wrap">{memoryAction.content}</p>
      </div>
      <p className={`text-xs mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
        确认后我会记住这条信息，之后给你推荐时会参考
      </p>
      <div className="flex gap-2">
        <button
          onClick={onConfirm}
          className="bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        >
          确认记住
        </button>
        <button
          onClick={onCancel}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-600'}`}
        >
          不要记住
        </button>
      </div>
    </div>
  );
}