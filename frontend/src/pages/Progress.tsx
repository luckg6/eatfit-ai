import { useState, useEffect } from 'react';
import { weightsAPI, bodyFatAPI, trainingsAPI } from '../api';
import { WeightRecord, BodyFatRecord, TrainingRecord } from '../types';
import dayjs from 'dayjs';

export default function Progress() {
  const [weights, setWeights] = useState<WeightRecord[]>([]);
  const [bodyFat, setBodyFat] = useState<BodyFatRecord[]>([]);
  const [trainings, setTrainings] = useState<TrainingRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'weight' | 'bodyfat' | 'training'>('weight');

  const [weightForm, setWeightForm] = useState({
    weight_kg: '',
    record_date: dayjs().format('YYYY-MM-DD'),
    note: '',
  });

  const [bodyFatForm, setBodyFatForm] = useState({
    body_fat_percent: '',
    record_date: dayjs().format('YYYY-MM-DD'),
    note: '',
  });

  const [trainingForm, setTrainingForm] = useState({
    training_type: '',
    duration_minutes: '',
    intensity: 'MODERATE',
    record_date: dayjs().format('YYYY-MM-DD'),
    note: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [weightsRes, bodyFatRes, trainingsRes] = await Promise.all([
        weightsAPI.list(),
        bodyFatAPI.list(),
        trainingsAPI.list(),
      ]);
      setWeights(weightsRes.data);
      setBodyFat(bodyFatRes.data);
      setTrainings(trainingsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddWeight = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await weightsAPI.create({
        weight_kg: parseFloat(weightForm.weight_kg),
        record_date: weightForm.record_date,
        note: weightForm.note || undefined,
      });
      setWeightForm({ weight_kg: '', record_date: dayjs().format('YYYY-MM-DD'), note: '' });
      loadData();
    } catch (error) {
      console.error('Failed to add weight:', error);
    }
  };

  const handleAddBodyFat = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await bodyFatAPI.create({
        body_fat_percent: parseFloat(bodyFatForm.body_fat_percent),
        record_date: bodyFatForm.record_date,
        note: bodyFatForm.note || undefined,
      });
      setBodyFatForm({ body_fat_percent: '', record_date: dayjs().format('YYYY-MM-DD'), note: '' });
      loadData();
    } catch (error) {
      console.error('Failed to add body fat:', error);
    }
  };

  const handleAddTraining = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await trainingsAPI.create({
        training_type: trainingForm.training_type,
        duration_minutes: trainingForm.duration_minutes ? parseInt(trainingForm.duration_minutes) : undefined,
        intensity: trainingForm.intensity,
        record_date: trainingForm.record_date,
        note: trainingForm.note || undefined,
      });
      setTrainingForm({
        training_type: '',
        duration_minutes: '',
        intensity: 'MODERATE',
        record_date: dayjs().format('YYYY-MM-DD'),
        note: '',
      });
      loadData();
    } catch (error) {
      console.error('Failed to add training:', error);
    }
  };

  const handleDelete = async (type: string, id: number) => {
    if (!confirm('确定要删除吗？')) return;
    try {
      if (type === 'weight') await weightsAPI.delete(id);
      else if (type === 'bodyfat') await bodyFatAPI.delete(id);
      else if (type === 'training') await trainingsAPI.delete(id);
      loadData();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const tabs = [
    { key: 'weight', label: '体重记录', icon: '⚖️' },
    { key: 'bodyfat', label: '体脂记录', icon: '📊' },
    { key: 'training', label: '训练记录', icon: '💪' },
  ] as const;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-800">进展记录</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                activeTab === tab.key
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center text-gray-500">加载中...</div>
        ) : (
          <div className="space-y-6">
            {activeTab === 'weight' && (
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-xl shadow-sm">
                  <h2 className="font-semibold text-gray-800 mb-4">记录体重</h2>
                  <form onSubmit={handleAddWeight} className="flex gap-4 items-end">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">体重 (kg)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={weightForm.weight_kg}
                        onChange={(e) => setWeightForm({ ...weightForm, weight_kg: e.target.value })}
                        className="w-32 px-4 py-2 border rounded-lg"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">日期</label>
                      <input
                        type="date"
                        value={weightForm.record_date}
                        onChange={(e) => setWeightForm({ ...weightForm, record_date: e.target.value })}
                        className="w-40 px-4 py-2 border rounded-lg"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">备注</label>
                      <input
                        type="text"
                        value={weightForm.note}
                        onChange={(e) => setWeightForm({ ...weightForm, note: e.target.value })}
                        className="w-40 px-4 py-2 border rounded-lg"
                        placeholder="可选"
                      />
                    </div>
                    <button type="submit" className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700">
                      添加
                    </button>
                  </form>
                </div>

                <div className="bg-white rounded-xl shadow-sm">
                  <div className="p-4 border-b">
                    <h2 className="font-semibold text-gray-800">体重历史</h2>
                  </div>
                  {weights.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">还没有体重记录</div>
                  ) : (
                    <div className="divide-y">
                      {weights.map((w) => (
                        <div key={w.id} className="p-4 flex justify-between items-center">
                          <div>
                            <span className="text-lg font-semibold text-gray-800">{w.weight_kg} kg</span>
                            <span className="text-gray-400 ml-2">{w.record_date}</span>
                            {w.note && <p className="text-sm text-gray-500">{w.note}</p>}
                          </div>
                          <button onClick={() => handleDelete('weight', w.id)} className="text-red-500 hover:text-red-700 text-sm">
                            删除
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'bodyfat' && (
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-xl shadow-sm">
                  <h2 className="font-semibold text-gray-800 mb-4">记录体脂</h2>
                  <form onSubmit={handleAddBodyFat} className="flex gap-4 items-end">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">体脂率 (%)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={bodyFatForm.body_fat_percent}
                        onChange={(e) => setBodyFatForm({ ...bodyFatForm, body_fat_percent: e.target.value })}
                        className="w-32 px-4 py-2 border rounded-lg"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">日期</label>
                      <input
                        type="date"
                        value={bodyFatForm.record_date}
                        onChange={(e) => setBodyFatForm({ ...bodyFatForm, record_date: e.target.value })}
                        className="w-40 px-4 py-2 border rounded-lg"
                        required
                      />
                    </div>
                    <button type="submit" className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700">
                      添加
                    </button>
                  </form>
                </div>

                <div className="bg-white rounded-xl shadow-sm">
                  <div className="p-4 border-b">
                    <h2 className="font-semibold text-gray-800">体脂历史</h2>
                  </div>
                  {bodyFat.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">还没有体脂记录</div>
                  ) : (
                    <div className="divide-y">
                      {bodyFat.map((bf) => (
                        <div key={bf.id} className="p-4 flex justify-between items-center">
                          <div>
                            <span className="text-lg font-semibold text-gray-800">{bf.body_fat_percent}%</span>
                            <span className="text-gray-400 ml-2">{bf.record_date}</span>
                          </div>
                          <button onClick={() => handleDelete('bodyfat', bf.id)} className="text-red-500 hover:text-red-700 text-sm">
                            删除
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'training' && (
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-xl shadow-sm">
                  <h2 className="font-semibold text-gray-800 mb-4">记录训练</h2>
                  <form onSubmit={handleAddTraining} className="space-y-4">
                    <div className="grid md:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">训练类型</label>
                        <input
                          type="text"
                          value={trainingForm.training_type}
                          onChange={(e) => setTrainingForm({ ...trainingForm, training_type: e.target.value })}
                          className="w-full px-4 py-2 border rounded-lg"
                          placeholder="力量训练"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">时长 (分钟)</label>
                        <input
                          type="number"
                          value={trainingForm.duration_minutes}
                          onChange={(e) => setTrainingForm({ ...trainingForm, duration_minutes: e.target.value })}
                          className="w-full px-4 py-2 border rounded-lg"
                          placeholder="60"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">强度</label>
                        <select
                          value={trainingForm.intensity}
                          onChange={(e) => setTrainingForm({ ...trainingForm, intensity: e.target.value })}
                          className="w-full px-4 py-2 border rounded-lg"
                        >
                          <option value="LIGHT">轻松</option>
                          <option value="MODERATE">中等</option>
                          <option value="HIGH">高强度</option>
                          <option value="MAX">极限</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">日期</label>
                        <input
                          type="date"
                          value={trainingForm.record_date}
                          onChange={(e) => setTrainingForm({ ...trainingForm, record_date: e.target.value })}
                          className="w-full px-4 py-2 border rounded-lg"
                          required
                        />
                      </div>
                    </div>
                    <button type="submit" className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700">
                      添加
                    </button>
                  </form>
                </div>

                <div className="bg-white rounded-xl shadow-sm">
                  <div className="p-4 border-b">
                    <h2 className="font-semibold text-gray-800">训练历史</h2>
                  </div>
                  {trainings.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">还没有训练记录</div>
                  ) : (
                    <div className="divide-y">
                      {trainings.map((t) => (
                        <div key={t.id} className="p-4 flex justify-between items-center">
                          <div>
                            <span className="font-semibold text-gray-800">{t.training_type}</span>
                            <span className="text-gray-400 ml-2">{t.record_date}</span>
                            <div className="text-sm text-gray-500 mt-1">
                              {t.duration_minutes && `${t.duration_minutes}分钟`}
                              {t.intensity && ` • ${t.intensity}`}
                            </div>
                          </div>
                          <button onClick={() => handleDelete('training', t.id)} className="text-red-500 hover:text-red-700 text-sm">
                            删除
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}