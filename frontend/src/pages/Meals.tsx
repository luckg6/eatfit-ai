import { useState, useEffect } from 'react';
import { mealsAPI } from '../api';
import { MealLog } from '../types';
import dayjs from 'dayjs';

const MEAL_TYPES = [
  { value: 'BREAKFAST', label: '早餐' },
  { value: 'LUNCH', label: '午餐' },
  { value: 'DINNER', label: '晚餐' },
  { value: 'SNACK', label: '加餐' },
  { value: 'POST_WORKOUT', label: '训练后' },
  { value: 'NIGHT_SNACK', label: '夜宵' },
];

const SCENARIOS = [
  { value: 'CANTEEN', label: '食堂' },
  { value: 'TAKEOUT', label: '外卖' },
  { value: 'CONVENIENCE_STORE', label: '便利店' },
  { value: 'FAST_FOOD', label: '快餐' },
  { value: 'RESTAURANT', label: '餐厅' },
  { value: 'HOME_COOKED', label: '自己做' },
  { value: 'PARTY', label: '聚餐' },
  { value: 'OTHER', label: '其他' },
];

export default function Meals() {
  const [meals, setMeals] = useState<MealLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState({
    meal_type: 'LUNCH',
    meal_time: dayjs().format('YYYY-MM-DDTHH:mm'),
    food_text: '',
    scenario: 'TAKEOUT',
    estimated_calories: '',
    estimated_protein: '',
    estimated_carbs: '',
    estimated_fat: '',
  });

  useEffect(() => {
    loadMeals();
  }, []);

  const loadMeals = async () => {
    try {
      const res = await mealsAPI.getToday();
      setMeals(res.data);
    } catch (error) {
      console.error('Failed to load meals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await mealsAPI.create({
        meal_type: formData.meal_type,
        meal_time: formData.meal_time,
        food_text: formData.food_text,
        scenario: formData.scenario,
        estimated_calories: formData.estimated_calories ? parseFloat(formData.estimated_calories) : null,
        estimated_protein: formData.estimated_protein ? parseFloat(formData.estimated_protein) : null,
        estimated_carbs: formData.estimated_carbs ? parseFloat(formData.estimated_carbs) : null,
        estimated_fat: formData.estimated_fat ? parseFloat(formData.estimated_fat) : null,
        sleep_impact: 'UNKNOWN',
      });
      setFormData({
        meal_type: 'LUNCH',
        meal_time: dayjs().format('YYYY-MM-DDTHH:mm'),
        food_text: '',
        scenario: 'TAKEOUT',
        estimated_calories: '',
        estimated_protein: '',
        estimated_carbs: '',
        estimated_fat: '',
      });
      setShowForm(false);
      loadMeals();
    } catch (error) {
      console.error('Failed to create meal:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这条记录吗？')) return;
    try {
      await mealsAPI.delete(id);
      loadMeals();
    } catch (error) {
      console.error('Failed to delete meal:', error);
    }
  };

  const getMealTypeLabel = (type: string) => {
    return MEAL_TYPES.find((t) => t.value === type)?.label || type;
  };

  const getScenarioLabel = (scenario: string) => {
    return SCENARIOS.find((s) => s.value === scenario)?.label || scenario;
  };

  const totalCalories = meals.reduce((sum, m) => sum + (m.estimated_calories || 0), 0);
  const totalProtein = meals.reduce((sum, m) => sum + (m.estimated_protein || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800">饮食记录</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            {showForm ? '取消' : '十 记录一餐'}
          </button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {showForm && (
          <div className="bg-white p-6 rounded-xl shadow-sm mb-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">餐次</label>
                  <select
                    value={formData.meal_type}
                    onChange={(e) => setFormData({ ...formData, meal_type: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg"
                  >
                    {MEAL_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">时间</label>
                  <input
                    type="datetime-local"
                    value={formData.meal_time}
                    onChange={(e) => setFormData({ ...formData, meal_time: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">吃了什么</label>
                <textarea
                  value={formData.food_text}
                  onChange={(e) => setFormData({ ...formData, food_text: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="描述你吃的食物，例如：牛肉饭 + 青菜 + 鸡蛋"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景</label>
                <select
                  value={formData.scenario}
                  onChange={(e) => setFormData({ ...formData, scenario: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg"
                >
                  {SCENARIOS.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">热量</label>
                  <input
                    type="number"
                    value={formData.estimated_calories}
                    onChange={(e) => setFormData({ ...formData, estimated_calories: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="kcal"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">蛋白质</label>
                  <input
                    type="number"
                    value={formData.estimated_protein}
                    onChange={(e) => setFormData({ ...formData, estimated_protein: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="g"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">碳水</label>
                  <input
                    type="number"
                    value={formData.estimated_carbs}
                    onChange={(e) => setFormData({ ...formData, estimated_carbs: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="g"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">脂肪</label>
                  <input
                    type="number"
                    value={formData.estimated_fat}
                    onChange={(e) => setFormData({ ...formData, estimated_fat: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="g"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700"
              >
                保存记录
              </button>
            </form>
          </div>
        )}

        <div className="bg-white p-6 rounded-xl shadow-sm mb-6">
          <h2 className="font-semibold text-gray-800 mb-4">今日营养估算</h2>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-primary-600">{totalCalories.toFixed(0)}</div>
              <div className="text-sm text-gray-500">总热量 (kcal)</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">{totalProtein.toFixed(0)}g</div>
              <div className="text-sm text-gray-500">蛋白质</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-600">
                {meals.reduce((sum, m) => sum + (m.estimated_carbs || 0), 0).toFixed(0)}g
              </div>
              <div className="text-sm text-gray-500">碳水</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-600">
                {meals.reduce((sum, m) => sum + (m.estimated_fat || 0), 0).toFixed(0)}g
              </div>
              <div className="text-sm text-gray-500">脂肪</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm">
          <div className="p-6 border-b">
            <h2 className="font-semibold text-gray-800">今日饮食</h2>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-500">加载中...</div>
          ) : meals.length === 0 ? (
            <div className="p-6 text-center text-gray-500">今天还没有记录饮食</div>
          ) : (
            <div className="divide-y">
              {meals.map((meal) => (
                <div key={meal.id} className="p-4 flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-800">
                        {getMealTypeLabel(meal.meal_type)}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                        {getScenarioLabel(meal.scenario)}
                      </span>
                      <span className="text-xs text-gray-400">
                        {dayjs(meal.meal_time).format('HH:mm')}
                      </span>
                    </div>
                    <p className="text-gray-600">{meal.food_text}</p>
                    {meal.ai_comment && (
                      <p className="text-sm text-primary-600 mt-1">AI: {meal.ai_comment}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right text-sm">
                      <div className="text-gray-800">{meal.estimated_calories || '-'} kcal</div>
                      <div className="text-gray-400">
                        P {meal.estimated_protein || 0}g / C {meal.estimated_carbs || 0}g / F {meal.estimated_fat || 0}g
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(meal.id)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}