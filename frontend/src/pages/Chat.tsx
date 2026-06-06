import { useState, useEffect, useRef } from 'react';
import { adviceAPI, mealsAPI, profileAPI, memoriesAPI, authAPI } from '../api';
import { ChatMessage, AgentStep } from '../types';
import ChatMessageList from '../components/chat/ChatMessageList';
import ChatInput from '../components/chat/ChatInput';
import ChatContextBar from '../components/chat/ChatContextBar';
import ProfileUpdateConfirmCard from '../components/chat/ProfileUpdateConfirmCard';
import MemoryConfirmCard from '../components/chat/MemoryConfirmCard';
import AgentTracePanel from '../components/chat/AgentTracePanel';
import { useTheme } from '../utils/ThemeContext';

interface TodaySummary {
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  meal_count: number;
}

interface ChatSession {
  id: number;
  title: string | null;
  scenario: string;
  is_training_day: boolean;
  created_at: string;
}

export default function Chat() {
  const { theme, toggleTheme } = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [scenario, setScenario] = useState('OTHER');
  const [isTrainingDay, setIsTrainingDay] = useState(false);
  const [contextCollapsed, setContextCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [todaySummary, setTodaySummary] = useState<TodaySummary | null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [agentTraceOpen, setAgentTraceOpen] = useState(false);
  const [traceSteps, setTraceSteps] = useState<AgentStep[]>([]);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
    loadTodaySummary();
    loadProfile();
    // 获取用户 GPS 位置
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          });
        },
        () => {}  // 拒绝或失败静默忽略
      );
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!userMenuOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Element;
      if (!target.closest('.user-menu')) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [userMenuOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadProfile = async () => {
    try {
      const res = await profileAPI.get();
      setProfile(res.data);
    } catch (e) {
      console.error('Failed to load profile', e);
    }
  };

  const loadTodaySummary = async () => {
    try {
      const res = await mealsAPI.getDailySummary();
      setTodaySummary({
        total_calories: res.data.total_calories || 0,
        total_protein: res.data.total_protein || 0,
        total_carbs: res.data.total_carbs || 0,
        total_fat: res.data.total_fat || 0,
        meal_count: res.data.meals?.length || 0,
      });
    } catch (e) {
      console.error('Failed to load today summary', e);
    }
  };

  const loadSessions = async () => {
    try {
      const res = await adviceAPI.getSessions(20);
      setSessions(res.data || []);
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  };

  const loadSessionMessages = async (sessionId: number) => {
    try {
      const res = await adviceAPI.getSessionMessages(sessionId);
      const msgs: ChatMessage[] = (res.data || []).map((m: any) => ({
        id: String(m.id),
        role: m.role as 'user' | 'assistant',
        content: m.content,
        created_at: m.created_at,
        action: m.action_type ? {
          type: m.action_type,
          data: m.action_data || {},
          status: m.action_status,
        } : undefined,
      }));
      setMessages(msgs);
      setCurrentSessionId(sessionId);
      setSidebarOpen(false);
      // Load session context
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        setScenario(session.scenario || 'OTHER');
        setIsTrainingDay(session.is_training_day || false);
      }
    } catch (e) {
      console.error('Failed to load session messages', e);
    }
  };

  const createNewSession = async () => {
    try {
      const res = await adviceAPI.createSession({
        title: '新对话',
        scenario,
        is_training_day: isTrainingDay,
      });
      setCurrentSessionId(res.data.id);
      setMessages([]);
      loadSessions();
      setSidebarOpen(false);
    } catch (e) {
      console.error('Failed to create session', e);
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    setIsLoading(true);
    setContextCollapsed(true);
    setTraceSteps([]);
    setAgentTraceOpen(true);

    // Optimistically add user message
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text.trim(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      // Use SSE endpoint for streaming
      let finalSessionId: number | null = null;
      const response = await adviceAPI.sendMessageStream({
        message: text.trim(),
        scenario,
        is_training_day: isTrainingDay,
        session_id: currentSessionId || undefined,
        latitude: userLocation?.latitude,
        longitude: userLocation?.longitude,
      });

      // Process SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentAiMessage: ChatMessage | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim();
            continue;
          }
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const event = JSON.parse(data);

              // Handle different SSE events
              if (event.step) {
                // Agent step event
                setTraceSteps(prev => [...prev, event]);
                continue;
              }

              if (event.intent) {
                // Intent detected
                setTraceSteps(prev => [...prev, {
                  step: 'intent_detected',
                  data: { intent: event.intent, confidence: event.confidence },
                  timestamp: new Date().toISOString()
                }]);
              }

              if (event.error) {
                // Server error event
                const errorMsg: ChatMessage = {
                  id: `error-${Date.now()}`,
                  role: 'assistant',
                  content: event.error || '抱歉，出了点问题。请稍后重试。',
                };
                setMessages(prev => [...prev, errorMsg]);
                continue;
              }

              if (event.message_id && event.action) {
                // Action pending - create message with pending action
                currentAiMessage = {
                  id: String(event.message_id),
                  role: 'assistant',
                  content: '', // Will be filled when message_done
                  action: {
                    type: event.action.action_type,
                    data: event.action.action_data,
                    status: 'pending'
                  }
                };
                setMessages(prev => [...prev, currentAiMessage]);
              } else if (event.message_id && event.session_id) {
                // message_done — always process, whether or not there's a pending action
                if (!currentAiMessage) {
                  // No pending action was created, make a new message
                  currentAiMessage = {
                    id: String(event.message_id),
                    role: 'assistant' as const,
                    content: event.content || '处理中...',
                  };
                  setMessages(prev => [...prev, currentAiMessage]);
                } else {
                  // Update existing message content
                  setMessages(prev => prev.map(m =>
                    m.id === currentAiMessage!.id
                      ? { ...m, content: event.content || currentAiMessage!.content || '处理中...' }
                      : m
                  ));
                }
                // Track session_id from server
                if (event.session_id) {
                  finalSessionId = event.session_id;
                }
              }

              if (event.memory_action) {
                // Memory pending confirmation.
                // 修 bug: 之前用 `mem-${Date.now()}` 合成 id，导致 handleConfirmMemory
                // 里 parseInt 拿到 NaN，PATCH /messages/{id} 永远 404。
                // 现在用 server 端 SSE 携带的真实 message_id（见 advice.py:282）。
                const serverMsgId = event.message_id;
                if (serverMsgId == null) {
                  console.warn('memory_pending event missing message_id; skipping');
                } else {
                  const memoryMsg: ChatMessage = {
                    id: String(serverMsgId),
                    role: 'assistant',
                    content: event.memory_action.display_text || '是否记住这条信息？',
                    action: {
                      type: 'memory_confirm',
                      data: event.memory_action,
                      status: 'pending'
                    }
                  };
                  setMessages(prev => [...prev, memoryMsg]);
                }
              }
            } catch (e) {
              // Ignore parse errors for partial data
            }
          }
        }
      }

      // Set session ID from server response
      if (finalSessionId) {
        setCurrentSessionId(finalSessionId);
      }

      // Reload sessions to show new one
      loadSessions();
      loadTodaySummary();
    } catch (err: any) {
      console.error('API error:', err);
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: err.response?.data?.detail || '抱歉，出了点问题。请稍后重试。',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setAgentTraceOpen(false);
    }
  };

  const handleConfirmMeal = async (messageId: string) => {
    const msg = messages.find((m) => m.id === messageId);
    if (!msg?.action?.data) return;

    try {
      await mealsAPI.create({
        meal_type: msg.action.data.meal_type || 'SNACK',
        food_text: msg.action.data.food_text || '',
        meal_time: msg.action.data.meal_time || null,  // Pass parsed meal_time
        scenario: msg.action.data.scenario || scenario,
        estimated_calories: msg.action.data.estimated_calories || 0,
        estimated_protein: msg.action.data.estimated_protein || 0,
        estimated_carbs: msg.action.data.estimated_carbs || 0,
        estimated_fat: msg.action.data.estimated_fat || 0,
        sleep_impact: 'NONE',
      });

      if (currentSessionId && msg.id) {
        const numericId = parseInt(msg.id, 10);
        // 只在 msg.id 是纯数字（server 真实 id）时 PATCH；防御性地跳过 NaN/非正数
        if (Number.isFinite(numericId) && numericId > 0) {
          try {
            await adviceAPI.updateMessage(currentSessionId, numericId, {
              // 后端 PATCH endpoint 复用了 ChatMessageCreate schema（role/content 必填），
              // 但 handler 实际只读 action_status/action_data。这里带上 role/content 占位
              // 才能通过 schema 校验。等后端改成 ChatMessageUpdate 后可去掉。
              role: msg.role,
              content: msg.content,
              action_status: 'confirmed',
            });
          } catch (e) {
            console.error('Failed to update message status', e);
          }
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, action: { ...m.action!, status: 'confirmed' } }
            : m
        )
      );

      loadTodaySummary();
    } catch (e) {
      console.error('Failed to log meal', e);
    }
  };

  const handleCancelMeal = (messageId: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId
          ? { ...m, action: { ...m.action!, status: 'cancelled' } }
          : m
      )
    );
  };

  const handleConfirmProfileUpdate = async (messageId: string) => {
    const msg = messages.find((m) => m.id === messageId);
    if (!msg?.action?.data?.updates) return;

    try {
      await profileAPI.update(msg.action.data.updates);

      if (currentSessionId && msg.id) {
        const numericId = parseInt(msg.id, 10);
        // 只在 msg.id 是纯数字（server 真实 id）时 PATCH；防御性地跳过 NaN/非正数
        if (Number.isFinite(numericId) && numericId > 0) {
          try {
            await adviceAPI.updateMessage(currentSessionId, numericId, {
              // 后端 PATCH endpoint 复用了 ChatMessageCreate schema（role/content 必填），
              // 但 handler 实际只读 action_status/action_data。这里带上 role/content 占位
              // 才能通过 schema 校验。等后端改成 ChatMessageUpdate 后可去掉。
              role: msg.role,
              content: msg.content,
              action_status: 'confirmed',
            });
          } catch (e) {
            console.error('Failed to update message status', e);
          }
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, action: { ...m.action!, status: 'confirmed' } }
            : m
        )
      );

      loadProfile();
    } catch (e) {
      console.error('Failed to update profile', e);
    }
  };

  const handleConfirmMemory = async (messageId: string) => {
    const msg = messages.find((m) => m.id === messageId);
    if (!msg?.action?.data) return;

    try {
      await memoriesAPI.create({
        memory_type: msg.action.data.memory_type,
        content: msg.action.data.content,
        importance_score: msg.action.data.importance_score || 5,
        source: 'chat',
        status: 'active',
      });

      if (currentSessionId && msg.id) {
        const numericId = parseInt(msg.id, 10);
        // 只在 msg.id 是纯数字（server 真实 id）时 PATCH；防御性地跳过 NaN/非正数
        if (Number.isFinite(numericId) && numericId > 0) {
          try {
            await adviceAPI.updateMessage(currentSessionId, numericId, {
              // 后端 PATCH endpoint 复用了 ChatMessageCreate schema（role/content 必填），
              // 但 handler 实际只读 action_status/action_data。这里带上 role/content 占位
              // 才能通过 schema 校验。等后端改成 ChatMessageUpdate 后可去掉。
              role: msg.role,
              content: msg.content,
              action_status: 'confirmed',
            });
          } catch (e) {
            console.error('Failed to update message status', e);
          }
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, action: { ...m.action!, status: 'confirmed' } }
            : m
        )
      );
    } catch (e) {
      console.error('Failed to save memory', e);
    }
  };

  const handleSelectRestaurant = async (messageId: string, restaurant: any) => {
    // Send message to agent loop with restaurant UID, so the agent can get details directly without re-searching
    const detailQuery = `帮我查看餐厅"${restaurant.name}"(UID:${restaurant.uid})的详细信息，分析是否符合我的饮食目标`;
    await handleSend(detailQuery);

    // Update message status to 'confirmed'
    if (currentSessionId && messageId && !messageId.startsWith('temp') && !messageId.startsWith('error') && !messageId.startsWith('loading')) {
      try {
        await adviceAPI.updateMessage(currentSessionId, parseInt(messageId), {
          action_status: 'confirmed',
        });
      } catch (e) {
        console.error('Failed to update restaurant message status', e);
      }
    }

    setMessages(prev =>
      prev.map(m =>
        m.id === messageId
          ? { ...m, action: { ...m.action!, status: 'confirmed' } }
          : m
      )
    );
  };

  const handleCancelRestaurant = (messageId: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId
          ? { ...m, action: { ...m.action!, status: 'cancelled' } }
          : m
      )
    );
  };

  const formatSessionDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '昨天';
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const getSessionPreview = (msg: ChatMessage) => {
    if (msg.role === 'user') return msg.content.slice(0, 30);
    // For assistant, get a snippet of the response
    const snippet = msg.content.slice(0, 40).replace(/\n/g, ' ');
    return snippet + (msg.content.length > 40 ? '...' : '');
  };

  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('确定删除这个会话？')) return;

    // Optimistic update
    const prevSessions = sessions;
    setSessions(sessions.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
      setMessages([]);
    }

    try {
      await adviceAPI.deleteSession(sessionId);
    } catch (err) {
      // Revert on failure
      setSessions(prevSessions);
      console.error('Failed to delete session', err);
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (e) {
      // Ignore backend errors, still logout locally
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  return (
    <div className={`h-screen flex ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'}`}>
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 flex flex-col ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'} border-r overflow-hidden flex-shrink-0`}>
        <div className="p-4 border-b border-gray-700 flex-shrink-0">
          <button
            onClick={createNewSession}
            className="w-full flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors font-medium"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            <p className={`px-3 py-2 text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>历史会话</p>
            {sessions.length === 0 ? (
              <p className={`px-3 py-2 text-sm ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>暂无历史会话</p>
            ) : (
              <div className="space-y-1">
                {sessions.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => loadSessionMessages(s.id)}
                    className={`w-full text-left px-3 py-3 rounded-lg transition-colors group cursor-pointer flex items-start gap-2 ${
                      currentSessionId === s.id
                        ? theme === 'dark' ? 'bg-gray-700 border border-gray-600' : 'bg-white border border-primary-200 shadow-sm'
                        : theme === 'dark' ? 'hover:bg-gray-700/50 border border-transparent' : 'hover:bg-gray-100 border border-transparent'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm truncate font-medium ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>
                        {s.title || '新对话'}
                      </p>
                      <p className={`text-xs mt-0.5 line-clamp-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                        {getSessionPreview(messages.find(m => m.id === String(s.id)) || { role: 'user', content: '' } as ChatMessage)}
                      </p>
                      <p className={`text-xs mt-1 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>{formatSessionDate(s.created_at)}</p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteSession(s.id, e)}
                      className={`opacity-0 group-hover:opacity-100 p-1.5 rounded-lg transition-all flex-shrink-0 ${theme === 'dark' ? 'hover:bg-gray-600 text-gray-400 hover:text-red-400' : 'hover:bg-gray-200 text-gray-400 hover:text-red-500'}`}
                      title="删除会话"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* User info at bottom */}
        <div className={`p-4 border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} flex-shrink-0 relative user-menu`}>
          <div
            className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
          >
            <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-medium">
              {profile?.nickname?.slice(0, 1) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm truncate font-medium ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>{profile?.nickname || '用户'}</p>
              <p className={`text-xs truncate ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{profile?.primary_goal || ''}</p>
            </div>
            <svg className={`w-4 h-4 transition-transform ${userMenuOpen ? 'rotate-180' : ''} ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>

          {userMenuOpen && (
            <div className={`absolute bottom-full left-0 right-0 mb-1 py-1 rounded-lg shadow-lg ${theme === 'dark' ? 'bg-gray-700 border border-gray-600' : 'bg-white border border-gray-200'}`}>
              <button
                onClick={handleLogout}
                className={`w-full flex items-center gap-2 px-4 py-2 text-sm text-left hover:bg-opacity-80 transition-colors ${theme === 'dark' ? 'text-gray-200 hover:bg-gray-600' : 'text-gray-700 hover:bg-gray-100'}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                退出登录
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className={`border-b px-4 py-3 flex items-center gap-4 flex-shrink-0 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-200' : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <h1 className={`text-base font-semibold ${theme === 'dark' ? 'text-gray-100' : 'text-gray-800'}`}>饮食助手</h1>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className={`ml-2 p-2 rounded-lg transition-colors ${theme === 'dark' ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-500'}`}
            title={theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
          >
            {theme === 'dark' ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          {todaySummary && (
            <div className="ml-auto flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>今日:</span>
                <span className={`font-semibold ${theme === 'dark' ? 'text-orange-400' : 'text-orange-500'}`}>{Math.round(todaySummary.total_calories)}</span>
                <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>kcal</span>
              </div>
              <div className="hidden sm:flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>蛋白质:</span>
                  <span className={`font-semibold ${theme === 'dark' ? 'text-green-400' : 'text-green-500'}`}>{Math.round(todaySummary.total_protein)}g</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>碳水:</span>
                  <span className={`font-semibold ${theme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'}`}>{Math.round(todaySummary.total_carbs)}g</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>脂肪:</span>
                  <span className={`font-semibold ${theme === 'dark' ? 'text-orange-400' : 'text-orange-500'}`}>{Math.round(todaySummary.total_fat)}g</span>
                </div>
              </div>
            </div>
          )}
        </header>

        {/* Context bar */}
        <ChatContextBar
          scenario={scenario}
          isTrainingDay={isTrainingDay}
          onScenarioChange={setScenario}
          onTrainingDayChange={setIsTrainingDay}
          collapsed={contextCollapsed}
          onToggleCollapse={() => setContextCollapsed(!contextCollapsed)}
          theme={theme}
        />

        {/* Messages */}
        <div className={`flex-1 overflow-y-auto ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 ${theme === 'dark' ? 'bg-gray-800' : 'bg-white shadow-sm'}`}>
                <span className="text-3xl">🍽️</span>
              </div>
              <h2 className={`text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>EatFit AI 饮食助手</h2>
              <p className={`text-sm max-w-md mb-6 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                描述你的饮食情况，获取个性化的饮食建议。试试说："我刚吃了牛肉饭"或"今天想吃点健康的"
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                {['我刚吃了牛肉饭', '今天训练完吃什么好', '推荐一个健康晚餐', '我有乳糖不耐能吃什么'].map((placeholder, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(placeholder)}
                    className={`px-4 py-2 text-sm rounded-full border transition-all ${theme === 'dark' ? 'bg-gray-800 hover:bg-gray-700 text-gray-300 border-gray-700 hover:border-gray-600' : 'bg-white hover:bg-gray-50 text-gray-600 border-gray-200 hover:border-primary-300'}`}
                  >
                    {placeholder}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <ChatMessageList
              messages={messages}
              onConfirmMeal={handleConfirmMeal}
              onCancelMeal={handleCancelMeal}
              onConfirmProfileUpdate={handleConfirmProfileUpdate}
              onCancelProfileUpdate={handleCancelMeal}
              onConfirmMemory={handleConfirmMemory}
              onCancelMemory={handleCancelMeal}
              onSelectRestaurant={handleSelectRestaurant}
              onCancelRestaurant={handleCancelRestaurant}
              theme={theme}
            />
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Agent Trace Panel - inline above input */}
        <AgentTracePanel
          steps={traceSteps}
          isOpen={agentTraceOpen}
          onToggle={() => setAgentTraceOpen(!agentTraceOpen)}
        />

        {/* Input */}
        <div className={`border-t px-4 py-4 flex-shrink-0 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSend={handleSend}
              disabled={isLoading}
              placeholder="描述你的饮食情况，获取建议..."
              theme={theme}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function formatAdviceAsText(data: any): string {
  if (!data) return '';

  let text = '';

  if (data.situation_summary) {
    text += `${data.situation_summary}\n\n`;
  }
  if (data.goal_analysis) {
    text += `${data.goal_analysis}\n\n`;
  }
  if (data.recommendation_strategy) {
    text += `${data.recommendation_strategy}\n\n`;
  }
  if (data.recommended_options?.length > 0) {
    data.recommended_options.forEach((opt: any, i: number) => {
      text += `${i + 1}. ${opt.name}`;
      if (opt.estimated_calories) text += ` (~${opt.estimated_calories}卡)`;
      text += `\n   ${opt.why_recommended}`;
      if (opt.order_modification) text += `\n   点餐建议: ${opt.order_modification}`;
      text += '\n';
    });
    text += '\n';
  }
  if (data.not_recommended?.length > 0) {
    data.not_recommended.forEach((opt: any) => {
      text += `❌ ${opt.name} - ${opt.reason}`;
      if (opt.better_alternative) text += `\n   更好的选择: ${opt.better_alternative}`;
      text += '\n';
    });
    text += '\n';
  }
  if (data.today_remaining_advice) {
    text += `📋 今日剩余: ${data.today_remaining_advice}\n\n`;
  }
  if (data.sleep_friendly_tips) {
    text += `😴 睡眠友好: ${data.sleep_friendly_tips}\n\n`;
  }
  if (data.training_day_tips) {
    text += `💪 训练日: ${data.training_day_tips}\n\n`;
  }
  if (data.next_meal_advice) {
    text += `🍽️ 下一餐: ${data.next_meal_advice}\n\n`;
  }
  if (data.one_sentence_summary) {
    text += `💡 ${data.one_sentence_summary}`;
  }

  return text.trim();
}