interface MealLogConfirmCardProps {
  parsedMeal: {
    food_text?: string;
    meal_type?: string;
    estimated_calories?: number;
    scenario?: string;
  };
  onConfirm: () => void;
  onCancel: () => void;
  theme?: 'light' | 'dark';
}

export default function MealLogConfirmCard({
  parsedMeal,
  onConfirm,
  onCancel,
  theme = 'dark',
}: MealLogConfirmCardProps) {
  const isDark = theme === 'dark';

  return (
    <div className={`ml-10 rounded-lg px-4 py-3 max-w-xs border ${isDark ? 'bg-blue-900/20 border-blue-700/30' : 'bg-blue-50 border-blue-200'}`}>
      <p className={`text-sm font-medium mb-2 ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>是否记录这餐?</p>
      <div className={`text-sm space-y-1 mb-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
        <p><span className={isDark ? 'text-gray-500' : 'text-gray-400'}>食物:</span> {parsedMeal.food_text}</p>
        {parsedMeal.meal_type && (
          <p><span className={isDark ? 'text-gray-500' : 'text-gray-400'}>餐次:</span> {parsedMeal.meal_type}</p>
        )}
        {parsedMeal.estimated_calories && (
          <p><span className={isDark ? 'text-gray-500' : 'text-gray-400'}>热量:</span> ~{parsedMeal.estimated_calories} kcal</p>
        )}
      </div>
      <div className="flex gap-2">
        <button
          onClick={onConfirm}
          className="bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        >
          确认
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