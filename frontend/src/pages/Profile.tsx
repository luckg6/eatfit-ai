import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../api';
import { UserFoodProfile } from '../types';

const GOALS = [
  { value: 'FAT_LOSS', label: '减脂' },
  { value: 'MUSCLE_GAIN', label: '增肌' },
  { value: 'MAINTAIN', label: '维持' },
  { value: 'SLEEP_FRIENDLY', label: '改善睡眠' },
  { value: 'LOW_SUGAR', label: '控糖' },
  { value: 'GENERAL_HEALTH', label: '普通健康' },
];

const ACTIVITY_LEVELS = [
  { value: 'SEDENTARY', label: '久坐（很少运动）' },
  { value: 'LIGHT', label: '轻度活动（每周1-2次运动）' },
  { value: 'MODERATE', label: '中等活动（每周3-4次运动）' },
  { value: 'ACTIVE', label: '高活动（每周5次以上运动）' },
];

export default function Profile() {
  const navigate = useNavigate();
  const [, setProfile] = useState<UserFoodProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const [formData, setFormData] = useState({
    nickname: '',
    gender: '',
    age: '',
    height_cm: '',
    weight_kg: '',
    body_fat_percent: '',
    target_weight_kg: '',
    primary_goal: 'GENERAL_HEALTH',
    activity_level: 'MODERATE',
    training_frequency: '',
    training_type: '',
    food_preferences: '',
    food_dislikes: '',
    allergies: '',
    budget_per_meal: '',
    common_eating_scenarios: '',
    sleep_sensitive: false,
    sleep_notes: '',
    notes: '',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const res = await profileAPI.get();
      setProfile(res.data);
      setFormData({
        nickname: res.data.nickname || '',
        gender: res.data.gender || '',
        age: res.data.age?.toString() || '',
        height_cm: res.data.height_cm?.toString() || '',
        weight_kg: res.data.weight_kg?.toString() || '',
        body_fat_percent: res.data.body_fat_percent?.toString() || '',
        target_weight_kg: res.data.target_weight_kg?.toString() || '',
        primary_goal: res.data.primary_goal || 'GENERAL_HEALTH',
        activity_level: res.data.activity_level || 'MODERATE',
        training_frequency: res.data.training_frequency?.toString() || '',
        training_type: res.data.training_type || '',
        food_preferences: res.data.food_preferences || '',
        food_dislikes: res.data.food_dislikes || '',
        allergies: res.data.allergies || '',
        budget_per_meal: res.data.budget_per_meal?.toString() || '',
        common_eating_scenarios: res.data.common_eating_scenarios || '',
        sleep_sensitive: res.data.sleep_sensitive || false,
        sleep_notes: res.data.sleep_notes || '',
        notes: res.data.notes || '',
      });
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const updateData = {
        nickname: formData.nickname || undefined,
        gender: formData.gender || undefined,
        age: formData.age ? parseInt(formData.age) : undefined,
        height_cm: formData.height_cm ? parseFloat(formData.height_cm) : undefined,
        weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : undefined,
        body_fat_percent: formData.body_fat_percent ? parseFloat(formData.body_fat_percent) : undefined,
        target_weight_kg: formData.target_weight_kg ? parseFloat(formData.target_weight_kg) : undefined,
        primary_goal: formData.primary_goal || undefined,
        activity_level: formData.activity_level || undefined,
        training_frequency: formData.training_frequency ? parseInt(formData.training_frequency) : undefined,
        training_type: formData.training_type || undefined,
        food_preferences: formData.food_preferences || undefined,
        food_dislikes: formData.food_dislikes || undefined,
        allergies: formData.allergies || undefined,
        budget_per_meal: formData.budget_per_meal ? parseFloat(formData.budget_per_meal) : undefined,
        common_eating_scenarios: formData.common_eating_scenarios || undefined,
        sleep_sensitive: formData.sleep_sensitive,
        sleep_notes: formData.sleep_notes || undefined,
        notes: formData.notes || undefined,
      };
      const res = await profileAPI.update(updateData);
      setProfile(res.data);
      setMessage('保存成功！');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (error) {
      setMessage('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div>加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-800">我的饮食画像</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-6">
          {message && (
            <div className={`p-4 rounded-lg ${message.includes('成功') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {message}
            </div>
          )}

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">基本信息</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">昵称</label>
                <input
                  type="text"
                  name="nickname"
                  value={formData.nickname}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="你怎么称呼"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">性别</label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                >
                  <option value="">未选择</option>
                  <option value="male">男</option>
                  <option value="female">女</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">年龄</label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="25"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">身高 (cm)</label>
                <input
                  type="number"
                  name="height_cm"
                  value={formData.height_cm}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="170"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">体重 (kg)</label>
                <input
                  type="number"
                  name="weight_kg"
                  value={formData.weight_kg}
                  onChange={handleChange}
                  step="0.1"
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="65"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">体脂率 (%)</label>
                <input
                  type="number"
                  name="body_fat_percent"
                  value={formData.body_fat_percent}
                  onChange={handleChange}
                  step="0.1"
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">目标体重 (kg)</label>
                <input
                  type="number"
                  name="target_weight_kg"
                  value={formData.target_weight_kg}
                  onChange={handleChange}
                  step="0.1"
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="60"
                />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">目标与运动</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">主要目标</label>
                <select
                  name="primary_goal"
                  value={formData.primary_goal}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                >
                  {GOALS.map((g) => (
                    <option key={g.value} value={g.value}>{g.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">活动水平</label>
                <select
                  name="activity_level"
                  value={formData.activity_level}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                >
                  {ACTIVITY_LEVELS.map((a) => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                  ))}
                </select>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">每周训练次数</label>
                  <input
                    type="number"
                    name="training_frequency"
                    value={formData.training_frequency}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="3"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">训练类型</label>
                  <input
                    type="text"
                    name="training_type"
                    value={formData.training_type}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border rounded-lg"
                    placeholder="力量训练、跑步等"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">饮食偏好</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">喜欢吃什么</label>
                <textarea
                  name="food_preferences"
                  value={formData.food_preferences}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="牛肉饭、鸡腿饭、鱼虾等"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">不喜欢吃什么</label>
                <textarea
                  name="food_dislikes"
                  value={formData.food_dislikes}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="香菜、青椒等"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">过敏/忌口</label>
                <input
                  type="text"
                  name="allergies"
                  value={formData.allergies}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="海鲜过敏等"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">每餐预算 (元)</label>
                <input
                  type="number"
                  name="budget_per_meal"
                  value={formData.budget_per_meal}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="30"
                />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="font-semibold text-lg text-gray-800 mb-4">睡眠与场景</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="sleep_sensitive"
                  checked={formData.sleep_sensitive}
                  onChange={handleChange}
                  className="w-4 h-4"
                />
                <label className="text-sm font-medium text-gray-700">我的睡眠容易被饮食影响</label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">睡眠相关说明</label>
                <textarea
                  name="sleep_notes"
                  value={formData.sleep_notes}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="晚上喝咖啡会睡不着"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">常见饮食场景</label>
                <input
                  type="text"
                  name="common_eating_scenarios"
                  value={formData.common_eating_scenarios}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="外卖、食堂、便利店"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="其他想告诉 AI 的信息"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full bg-primary-600 text-white py-3 rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? '保存中...' : '保存'}
          </button>
        </form>
      </main>
    </div>
  );
}