import { Restaurant } from '../../types';

interface RestaurantConfirmCardProps {
  restaurants: Restaurant[];
  onSelect: (restaurant: Restaurant) => void;
  onCancel: () => void;
  theme?: 'light' | 'dark';
}

export default function RestaurantConfirmCard({
  restaurants,
  onSelect,
  onCancel,
  theme = 'dark',
}: RestaurantConfirmCardProps) {
  const isDark = theme === 'dark';

  return (
    <div className={`ml-10 rounded-lg px-4 py-3 max-w-md border ${isDark ? 'bg-blue-900/20 border-blue-700/30' : 'bg-blue-50 border-blue-200'}`}>
      <p className={`text-sm font-medium mb-3 ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
        📍 附近餐厅推荐
      </p>

      <div className="space-y-2 mb-4">
        {restaurants.map((restaurant, index) => (
          <div
            key={restaurant.uid || index}
            className={`p-3 rounded-lg border cursor-pointer hover:border-primary-500 transition-colors ${
              isDark ? 'bg-gray-800 border-gray-700 hover:bg-gray-750' : 'bg-white border-gray-200 hover:border-primary-400'
            }`}
            onClick={() => onSelect(restaurant)}
          >
            <div className="flex justify-between items-start">
              <div>
                <p className={`font-medium ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                  {index + 1}. {restaurant.name}
                </p>
                {restaurant.tag && (
                  <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {restaurant.tag}
                  </p>
                )}
              </div>
              {restaurant.rating && (
                <span className={`text-sm font-medium px-2 py-0.5 rounded ${
                  isDark ? 'bg-yellow-900/30 text-yellow-400' : 'bg-yellow-100 text-yellow-600'
                }`}>
                  ⭐ {restaurant.rating}
                </span>
              )}
            </div>
            {restaurant.address && (
              <p className={`text-xs mt-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                📍 {restaurant.address}
              </p>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-600'}`}
        >
          关闭
        </button>
      </div>
    </div>
  );
}