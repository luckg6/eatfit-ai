import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      <header className="container mx-auto px-4 py-6">
        <nav className="flex justify-between items-center">
          <div className="text-2xl font-bold text-primary-600">EatFit AI</div>
          <div className="space-x-4">
            <Link to="/login" className="text-gray-600 hover:text-primary-600">登录</Link>
            <Link
              to="/register"
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
            >
              开始使用
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="container mx-auto px-4 py-20 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-6">
            不知道今天中午吃什么？
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            EatFit AI 帮你在外食场景中做出更健康的选择。
            不用复杂算卡路里，也能把方向吃对。
          </p>
          <Link
            to="/register"
            className="inline-block bg-primary-600 text-white text-lg px-8 py-3 rounded-xl hover:bg-primary-700 shadow-lg"
          >
            开始你的健康饮食之旅
          </Link>
        </section>

        <section className="container mx-auto px-4 py-16">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">🍽️</div>
              <h3 className="text-xl font-semibold mb-2">外食也能增肌减脂</h3>
              <p className="text-gray-600">不管是外卖、食堂还是便利店，都能给你合适的建议</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">🧠</div>
              <h3 className="text-xl font-semibold mb-2">记住你的喜好</h3>
              <p className="text-gray-600">长期学习你的饮食偏好、训练习惯和睡眠特点</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">每周复盘进步</h3>
              <p className="text-gray-600">追踪你的饮食和体重变化，持续优化策略</p>
            </div>
          </div>
        </section>

        <section className="container mx-auto px-4 py-16 bg-gray-50 rounded-3xl">
          <h2 className="text-2xl font-bold text-center mb-8">产品特点</h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            <div className="flex items-start gap-3">
              <span className="text-green-500">✓</span>
              <span>不用精确称重，也能做出更好的选择</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-green-500">✓</span>
              <span>根据你的目标、口味、训练和睡眠情况推荐</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-green-500">✓</span>
              <span>每次选择都比昨天更好一点</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-green-500">✓</span>
              <span>不制造焦虑，只帮你多做一个更优选择</span>
            </div>
          </div>
        </section>

        <section className="container mx-auto px-4 py-16">
          <div className="bg-primary-600 text-white rounded-2xl p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">让 EatFit AI 帮你</h2>
            <p className="text-primary-100 mb-6">
              输入你的情况，AI 帮你分析这顿饭怎么吃更健康
            </p>
            <Link
              to="/register"
              className="inline-block bg-white text-primary-600 font-semibold px-6 py-3 rounded-lg hover:bg-gray-100"
            >
              免费开始使用
            </Link>
          </div>
        </section>
      </main>

      <footer className="container mx-auto px-4 py-8 text-center text-gray-500">
        <p>EatFit AI - 外食健康饮食助手</p>
      </footer>
    </div>
  );
}