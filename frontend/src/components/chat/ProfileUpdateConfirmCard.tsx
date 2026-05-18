interface ProfileUpdateConfirmCardProps {
  updates: Record<string, any>;
  oldValues: Record<string, any>;
  onConfirm: () => void;
  onCancel: () => void;
  theme?: 'light' | 'dark';
}

export default function ProfileUpdateConfirmCard({
  updates,
  oldValues,
  onConfirm,
  onCancel,
  theme = 'dark',
}: ProfileUpdateConfirmCardProps) {
  const isDark = theme === 'dark';
  const fieldNames: Record<string, string> = {
    weight_kg: "体重",
    budget_per_meal: "预算",
    gender: "性别",
    age: "年龄",
    primary_goal: "目标",
    height_cm: "身高",
    target_weight_kg: "目标体重",
  };

  const formatValue = (key: string, value: any): string => {
    if (key === "weight_kg" || key === "target_weight_kg" || key === "height_cm") {
      return `${value}kg`;
    }
    if (key === "budget_per_meal") {
      return `${value}元/餐`;
    }
    if (key === "primary_goal") {
      const goalNames: Record<string, string> = {
        FAT_LOSS: "减脂",
        MUSCLE_GAIN: "增肌",
        MAINTAIN: "维持",
        SUGAR_CONTROL: "控糖",
        SLEEP_IMPROVEMENT: "改善睡眠",
        GENERAL_HEALTH: "一般健康",
      };
      return goalNames[value] || value;
    }
    return String(value);
  };

  return (
    <div className={`ml-10 rounded-lg px-4 py-3 max-w-xs border ${isDark ? 'bg-purple-900/20 border-purple-700/30' : 'bg-purple-50 border-purple-200'}`}>
      <p className={`text-sm font-medium mb-2 ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>检测到资料更新</p>
      <div className={`text-sm space-y-1 mb-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
        {Object.entries(updates).map(([key, newValue]) => {
          const oldValue = oldValues[key];
          const displayName = fieldNames[key] || key;
          return (
            <p key={key}>
              <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>{displayName}:</span>{" "}
              {oldValue !== undefined && oldValue !== null
                ? `${formatValue(key, oldValue)} → `
                : ""}
              <span className={isDark ? 'text-purple-300 font-medium' : 'text-purple-600 font-medium'}>{formatValue(key, newValue)}</span>
            </p>
          );
        })}
      </div>
      <p className={`text-xs mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>确认后资料将更新</p>
      <div className="flex gap-2">
        <button
          onClick={onConfirm}
          className="bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        >
          确认更新
        </button>
        <button
          onClick={onCancel}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-600'}`}
        >
          取消
        </button>
      </div>
    </div>
  );
}