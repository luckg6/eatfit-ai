import { useRef, useEffect } from 'react';
import { ChatMessage } from '../../types';
import MealLogConfirmCard from './MealLogConfirmCard';
import ProfileUpdateConfirmCard from './ProfileUpdateConfirmCard';
import MemoryConfirmCard from './MemoryConfirmCard';
import RestaurantConfirmCard from './RestaurantConfirmCard';

interface ChatMessageListProps {
  messages: ChatMessage[];
  onConfirmMeal: (messageId: string) => void;
  onCancelMeal: (messageId: string) => void;
  onConfirmProfileUpdate?: (messageId: string) => void;
  onCancelProfileUpdate?: (messageId: string) => void;
  onConfirmMemory?: (messageId: string) => void;
  onCancelMemory?: (messageId: string) => void;
  onSelectRestaurant?: (messageId: string, restaurant: any) => void;
  onCancelRestaurant?: (messageId: string) => void;
  theme?: 'light' | 'dark';
}

export default function ChatMessageList({
  messages,
  onConfirmMeal,
  onCancelMeal,
  onConfirmProfileUpdate,
  onCancelProfileUpdate,
  onConfirmMemory,
  onCancelMemory,
  onSelectRestaurant,
  onCancelRestaurant,
  theme = 'dark',
}: ChatMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const renderConfirmedStatus = (msg: ChatMessage) => {
    if (msg.action?.status !== 'confirmed') return null;

    const actionType = msg.action.type;
    const data = msg.action.data;

    if (actionType === 'meal_log') {
      return (
        <div className="flex justify-start ml-10">
          <div className={`px-4 py-2 rounded-lg text-sm border ${isDark ? 'bg-green-900/30 text-green-400 border-green-800/30' : 'bg-green-50 text-green-600 border-green-200'}`}>
            ✓ 已记录: {data.food_text}
          </div>
        </div>
      );
    }
    if (actionType === 'profile_update') {
      return (
        <div className="flex justify-start ml-10">
          <div className={`px-4 py-2 rounded-lg text-sm border ${isDark ? 'bg-green-900/30 text-green-400 border-green-800/30' : 'bg-green-50 text-green-600 border-green-200'}`}>
            ✓ 已更新资料
          </div>
        </div>
      );
    }
    if (actionType === 'memory_confirm') {
      return (
        <div className="flex justify-start ml-10">
          <div className={`px-4 py-2 rounded-lg text-sm border ${isDark ? 'bg-green-900/30 text-green-400 border-green-800/30' : 'bg-green-50 text-green-600 border-green-200'}`}>
            ✓ 已记住
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 px-4 py-6">
      {messages.map((msg) => (
        <div key={msg.id} className="space-y-2">
          {msg.role === 'user' ? (
            <div className="flex justify-end">
              <div className="bg-primary-600 text-white px-4 py-3 rounded-2xl rounded-br-md max-w-xs md:max-w-md">
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ) : (
            <div className="flex justify-start">
              <div className="flex gap-3 max-w-lg">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${isDark ? 'bg-gray-700' : 'bg-primary-100'}`}>
                  <span className="text-sm">🍽️</span>
                </div>
                <div className={`px-4 py-3 rounded-2xl rounded-bl-md border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200 shadow-sm'}`}>
                  <p className={`text-sm whitespace-pre-wrap leading-relaxed ${isDark ? 'text-gray-200' : 'text-gray-700'}`}>{msg.content}</p>
                </div>
              </div>
            </div>
          )}

          {msg.action?.type === 'meal_log' && msg.action.status === 'pending' && (
            <MealLogConfirmCard
              parsedMeal={msg.action.data}
              onConfirm={() => onConfirmMeal(msg.id)}
              onCancel={() => onCancelMeal(msg.id)}
              theme={theme}
            />
          )}

          {msg.action?.type === 'profile_update' && msg.action.status === 'pending' && onConfirmProfileUpdate && (
            <ProfileUpdateConfirmCard
              updates={msg.action.data.updates || {}}
              oldValues={msg.action.data.old_values || {}}
              onConfirm={() => onConfirmProfileUpdate(msg.id)}
              onCancel={() => onCancelProfileUpdate?.(msg.id)}
              theme={theme}
            />
          )}

          {msg.action?.type === 'memory_confirm' && msg.action.status === 'pending' && onConfirmMemory && (
            <MemoryConfirmCard
              memoryAction={msg.action.data}
              onConfirm={() => onConfirmMemory(msg.id)}
              onCancel={() => onCancelMemory?.(msg.id)}
              theme={theme}
            />
          )}

          {msg.action?.type === 'restaurant_select' && msg.action.status === 'pending' && msg.action.data.restaurants && (
            <RestaurantConfirmCard
              restaurants={msg.action.data.restaurants}
              onSelect={(restaurant) => onSelectRestaurant?.(msg.id, restaurant)}
              onCancel={() => onCancelRestaurant?.(msg.id)}
              theme={theme}
            />
          )}

          {renderConfirmedStatus(msg)}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}