import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { profileAPI, mealsAPI, adviceAPI, memoriesAPI, weightsAPI } from '../api';
import { UserFoodProfile, MealLog, MemoryItem } from '../types';

export default function Dashboard() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserFoodProfile | null>(null);
  const [todayMeals, setTodayMeals] = useState<MealLog[]>([]);
  const [todaySummary, setTodaySummary] = useState<any>(null);
  const [recentAdvices, setRecentAdvices] = useState<any[]>([]);
  const [importantMemories, setImportantMemories] = useState<MemoryItem[]>([]);
  const [recentWeights, setRecentWeights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [profileRes, mealsRes, summaryRes, historyRes, memoriesRes, weightsRes] = await Promise.all([
        profileAPI.get().catch(() => ({ data: null })),
        mealsAPI.getToday().catch(() => ({ data: [] })),
        mealsAPI.getDailySummary().catch(() => ({ data: null })),
        adviceAPI.getHistory(5).catch(() => ({ data: [] })),
        memoriesAPI.list().catch(() => ({ data: [] })),
        weightsAPI.list(3).catch(() => ({ data: [] })),
      ]);

      setProfile(profileRes.data);
      setTodayMeals(mealsRes.data || []);
      setTodaySummary(summaryRes.data);
      setRecentAdvices(historyRes.data || []);
      setImportantMemories((memoriesRes.data || []).filter((m: MemoryItem) => m.importance_score >= 7).slice(0, 3));
      setRecentWeights(weightsRes.data || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGoalLabel = (goal: string) => {
    const labels: Record<string, string> = {
      FAT_LOSS: '减脂',
      MUSCLE_GAIN: '增肌',
      MAINTAIN: '维持',
      SLEEP_FRIENDLY: '改善睡眠',
      LOW_SUGAR: '控糖',
      GENERAL_HEALTH: '普通健康',
    };
    return labels[goal] || goal;
  };

  const getMealTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      BREAKFAST: '早餐',
      LUNCH: '午餐',
      DINNER: '晚餐',
      SNACK: '加餐',
      POST_WORKOUT: '训练后',
      NIGHT_SNACK: '夜宵',
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="text-xl font-bold text-primary-600">EatFit AI</div>
          <nav className="flex items-center gap-4">
            <Link to="/chat" className="text-gray-600 hover:text-primary-600">
              今天吃什么
            </Link>
            <Link to="/profile" className="text-gray-600 hover:text-primary-600">
              我的画像
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-800">
            你好，{profile?.nickname || user?.username || '用户'} 👋
          </h1>
          {profile?.primary_goal && (
            <p className="text-gray-600 mt-1">
              当前目标：{getGoalLabel(profile.primary_goal)}
            </p>
          )}
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link
            to="/chat"
            className="bg-primary-600 text-white p-6 rounded-xl hover:bg-primary-700"
          >
            <div className="text-2xl mb-2">🍽️</div>
            <h3 className="font-semibold text-lg">今天吃什么？</h3>
            <p className="text-primary-100 text-sm mt-1">让 AI 帮你分析建议</p>
          </Link>

          <Link
            to="/meals"
            className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md"
          >
            <div className="text-2xl mb-2">📝</div>
            <h3 className="font-semibold text-lg text-gray-800">记录一餐</h3>
            <p className="text-gray-500 text-sm mt-1">记录你吃了什么</p>
          </Link>

          <Link
            to="/weekly-review"
            className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md"
          >
            <div className="text-2xl mb-2">📊</div>
            <h3 className="font-semibold text-lg text-gray-800">一周复盘</h3>
            <p className="text-gray-500 text-sm mt-1">回顾本周饮食</p>
          </Link>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">今日饮食</h2>
            {todayMeals.length === 0 ? (
              <p className="text-gray-500">今天还没有记录饮食</p>
            ) : (
              <div className="space-y-3">
                {todayMeals.map((meal) => (
                  <div key={meal.id} className="flex justify-between items-center border-b pb-3">
                    <div>
                      <span className="font-medium text-gray-700">
                        {getMealTypeLabel(meal.meal_type)}
                      </span>
                      <p className="text-gray-600 text-sm">{meal.food_text}</p>
                    </div>
                    <span className="text-gray-500 text-sm">
                      {meal.estimated_calories}卡
                    </span>
                  </div>
                ))}
              </div>
            )}
            {todaySummary && (
              <div className="mt-4 pt-4 border-t grid grid-cols-4 gap-2 text-center">
                <div>
                  <div className="text-lg font-semibold text-primary-600">
                    {todaySummary.total_calories.toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-500">热量</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-green-600">
                    {todaySummary.total_protein.toFixed(0)}g
                  </div>
                  <div className="text-xs text-gray-500">蛋白质</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-yellow-600">
                    {todaySummary.total_carbs.toFixed(0)}g
                  </div>
                  <div className="text-xs text-gray-500">碳水</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-orange-600">
                    {todaySummary.total_fat.toFixed(0)}g
                  </div>
                  <div className="text-xs text-gray-500">脂肪</div>
                </div>
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">重要记忆</h2>
            {importantMemories.length === 0 ? (
              <p className="text-gray-500">还没有记忆，AI 会自动学习</p>
            ) : (
              <div className="space-y-3">
                {importantMemories.map((mem) => (
                  <div key={mem.id} className="p-3 bg-gray-50 rounded-lg">
                    <span className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded">
                      {mem.memory_type}
                    </span>
                    <p className="text-gray-700 mt-2">{mem.content}</p>
                  </div>
                ))}
              </div>
            )}
            <Link
              to="/memories"
              className="mt-4 text-primary-600 text-sm hover:underline"
            >
              查看全部记忆 →
            </Link>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">最近体重</h2>
            {recentWeights.length === 0 ? (
              <p className="text-gray-500">
                还没有体重记录{' '}
                <Link to="/progress" className="text-primary-600 hover:underline">
                  去记录
                </Link>
              </p>
            ) : (
              <div className="space-y-2">
                {recentWeights.map((w) => (
                  <div key={w.id} className="flex justify-between items-center">
                    <span className="text-gray-600">{w.record_date}</span>
                    <span className="font-semibold text-gray-800">{w.weight_kg} kg</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">最近建议</h2>
            {recentAdvices.length === 0 ? (
              <p className="text-gray-500">还没有咨询记录</p>
            ) : (
              <div className="space-y-3">
                {recentAdvices.map((adv) => (
                  <div key={adv.id} className="border-b pb-3">
                    <p className="text-gray-700 text-sm">{adv.user_question}</p>
                    <p className="text-gray-400 text-xs mt-1">{adv.created_at}</p>
                  </div>
                ))}
              </div>
            )}
            <Link
              to="/chat"
              className="mt-4 text-primary-600 text-sm hover:underline"
            >
              查看更多 →
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}