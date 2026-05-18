interface ChatContextBarProps {
  scenario: string;
  isTrainingDay: boolean;
  onScenarioChange: (s: string) => void;
  onTrainingDayChange: (b: boolean) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  theme?: 'light' | 'dark';
}

const SCENARIOS = [
  { value: 'CANTEEN', label: '食堂' },
  { value: 'DELIVERY', label: '外卖' },
  { value: 'CONVENIENCE', label: '便利店' },
  { value: 'FAST_FOOD', label: '快餐' },
  { value: 'RESTAURANT', label: '餐厅' },
  { value: 'DINNER_PARTY', label: '聚餐' },
  { value: 'OTHER', label: '其他' },
];

export default function ChatContextBar({
  scenario,
  isTrainingDay,
  onScenarioChange,
  onTrainingDayChange,
  collapsed = false,
  onToggleCollapse,
  theme = 'dark',
}: ChatContextBarProps) {
  const isDark = theme === 'dark';

  if (collapsed) {
    return (
      <div className={`px-4 py-2 border-b ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
        <button
          onClick={onToggleCollapse}
          className={`text-sm ${isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'}`}
        >
          场景: {SCENARIOS.find((s) => s.value === scenario)?.label || '其他'}
          {isTrainingDay && ' · 训练日'}
          <span className="ml-1 opacity-50">✎</span>
        </button>
      </div>
    );
  }

  return (
    <div className={`px-4 py-3 border-b ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center gap-6 max-w-3xl mx-auto">
        <div className="flex items-center gap-2">
          <label className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>场景</label>
          <select
            value={scenario}
            onChange={(e) => onScenarioChange(e.target.value)}
            className={`border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${isDark ? 'bg-gray-700 border-gray-600 text-gray-200' : 'bg-white border-gray-200 text-gray-700'}`}
          >
            {SCENARIOS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="training-day"
            checked={isTrainingDay}
            onChange={(e) => onTrainingDayChange(e.target.checked)}
            className={`w-4 h-4 rounded ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'} text-primary-600 focus:ring-primary-500`}
          />
          <label htmlFor="training-day" className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>训练日</label>
        </div>
      </div>
    </div>
  );
}