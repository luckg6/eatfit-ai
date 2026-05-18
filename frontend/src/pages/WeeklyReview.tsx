import { useState } from 'react';
import { Link } from 'react-router-dom';
import { adviceAPI } from '../api';
import { WeeklyReviewResponse } from '../types';

export default function WeeklyReview() {
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState<WeeklyReviewResponse | null>(null);
  const [error, setError] = useState('');

  const generateReview = async () => {
    setLoading(true);
    setError('');
    setReview(null);
    try {
      const res = await adviceAPI.generateWeeklyReview();
      setReview(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '生成复盘失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-800">一周饮食复盘</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          {!review && !loading && (
            <div className="bg-white p-8 rounded-xl shadow-sm text-center">
              <div className="text-4xl mb-4">📊</div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">生成你的每周饮食报告</h2>
              <p className="text-gray-600 mb-6">
                基于你的饮食记录、训练数据和体重变化，生成个性化的周报
              </p>
              <button
                onClick={generateReview}
                className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700"
              >
                生成复盘
              </button>
            </div>
          )}

          {loading && (
            <div className="bg-white p-8 rounded-xl shadow-sm text-center">
              <div className="text-gray-600">生成中...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {review && (
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-xl shadow-sm">
                <h2 className="font-semibold text-lg text-gray-800 mb-2">本周总结</h2>
                <p className="text-gray-600">{review.week_summary}</p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm">
                  <h3 className="font-semibold text-green-600 mb-3">做得好的地方</h3>
                  <ul className="space-y-2">
                    {review.what_went_well.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-gray-700">
                        <span className="text-green-500">✓</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm">
                  <h3 className="font-semibold text-orange-600 mb-3">主要问题</h3>
                  <ul className="space-y-2">
                    {review.main_problems.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-gray-700">
                        <span className="text-orange-500">!</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-3">蛋白质摄入</h3>
                <p className="text-gray-600">{review.protein_consistency}</p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-3">睡眠影响分析</h3>
                <p className="text-gray-600">{review.sleep_impact_analysis}</p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-3">外食模式</h3>
                <p className="text-gray-600">{review.eating_out_pattern}</p>
              </div>

              {review.weight_and_body_fat_trend && (
                <div className="bg-white p-6 rounded-xl shadow-sm">
                  <h3 className="font-semibold text-gray-800 mb-3">体重和体脂趋势</h3>
                  <p className="text-gray-600">{review.weight_and_body_fat_trend}</p>
                </div>
              )}

              <div className="bg-primary-50 p-6 rounded-xl">
                <h3 className="font-semibold text-primary-800 mb-3">下周策略</h3>
                <p className="text-primary-700">{review.next_week_strategy}</p>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-3">下周行动清单</h3>
                <ul className="space-y-2">
                  {review.next_week_actions.map((action, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <span className="bg-primary-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                        {i + 1}
                      </span>
                      {action}
                    </li>
                  ))}
                </ul>
              </div>

              {review.warnings.length > 0 && (
                <div className="bg-yellow-50 p-6 rounded-xl">
                  <h3 className="font-semibold text-yellow-800 mb-3">提醒</h3>
                  <ul className="list-disc list-inside text-yellow-700">
                    {review.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex gap-4">
                <Link
                  to="/chat"
                  className="flex-1 bg-primary-600 text-white text-center py-3 rounded-lg hover:bg-primary-700"
                >
                  去咨询
                </Link>
                <button
                  onClick={generateReview}
                  className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300"
                >
                  重新生成
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}