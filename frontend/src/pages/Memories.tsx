import { useState, useEffect } from 'react';
import { memoriesAPI, userAPI } from '../api';
import { MemoryItem } from '../types';
import dayjs from 'dayjs';

const MEMORY_TYPES = [
  { value: '', label: '全部' },
  { value: 'diet_preference', label: '饮食偏好' },
  { value: 'food_dislike', label: '不喜欢食物' },
  { value: 'allergy_intolerance', label: '过敏/不耐受' },
  { value: 'goal', label: '长期目标' },
  { value: 'budget', label: '预算偏好' },
  { value: 'location', label: '常用位置' },
  { value: 'scenario', label: '饮食场景' },
  { value: 'sleep', label: '睡眠相关' },
  { value: 'body_response', label: '身体反应' },
  { value: 'restriction', label: '现实限制' },
  { value: 'habit', label: '饮食习惯' },
  { value: 'other', label: '其他' },
];

const STATUS_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'active', label: '激活' },
  { value: 'inactive', label: '已禁用' },
  { value: 'superseded', label: '已替代' },
  { value: 'pending', label: '待确认' },
];

export default function Memories() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [autoMemoryEnabled, setAutoMemoryEnabled] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    memory_type: 'diet_preference',
    content: '',
    importance_score: 5,
  });

  const [editFormData, setEditFormData] = useState({
    memory_type: '',
    content: '',
    importance_score: 5,
  });

  useEffect(() => {
    loadMemories();
  }, [filterType, filterStatus]);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filterType) params.memory_type = filterType;
      if (filterStatus) params.status = filterStatus;
      const res = await memoriesAPI.list(filterType || undefined);
      // Filter on client side for status (API may not support)
      let data = res.data;
      if (filterStatus) {
        data = data.filter((m: MemoryItem) => m.status === filterStatus);
      }
      setMemories(data);
    } catch (error) {
      console.error('Failed to load memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async (id: number) => {
    try {
      await memoriesAPI.delete(id);  // Soft delete - sets status to inactive
      loadMemories();
    } catch (error) {
      console.error('Failed to disable memory:', error);
    }
  };

  const handleEnable = async (id: number) => {
    try {
      await memoriesAPI.update(id, { status: 'active' });
      loadMemories();
    } catch (error) {
      console.error('Failed to enable memory:', error);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm('确定要清空所有激活的记忆吗？此操作不可撤销。')) return;
    try {
      await memoriesAPI.deleteAll();
      loadMemories();
    } catch (error) {
      console.error('Failed to delete all memories:', error);
    }
  };

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await memoriesAPI.create(formData);
      setFormData({ memory_type: 'diet_preference', content: '', importance_score: 5 });
      setShowAddForm(false);
      loadMemories();
    } catch (error) {
      console.error('Failed to add memory:', error);
    }
  };

  const handleEdit = (memory: MemoryItem) => {
    setEditingId(memory.id);
    setEditFormData({
      memory_type: memory.memory_type,
      content: memory.content,
      importance_score: memory.importance_score,
    });
  };

  const handleUpdateMemory = async (id: number) => {
    try {
      await memoriesAPI.update(id, {
        memory_type: editFormData.memory_type,
        content: editFormData.content,
        importance_score: editFormData.importance_score,
      });
      setEditingId(null);
      loadMemories();
    } catch (error) {
      console.error('Failed to update memory:', error);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
  };

  const toggleAutoMemory = async () => {
    try {
      await userAPI.updateAutoMemory(!autoMemoryEnabled);
      setAutoMemoryEnabled(!autoMemoryEnabled);
    } catch (error) {
      console.error('Failed to update auto memory setting:', error);
    }
  };

  const getTypeLabel = (type: string) => {
    return MEMORY_TYPES.find((t) => t.value === type)?.label || type;
  };

  const getSourceLabel = (source: string) => {
    const labels: Record<string, string> = {
      manual: '手动添加',
      auto_extracted: '自动提取',
      chat: '聊天记录',
    };
    return labels[source] || source;
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string }> = {
      active: { bg: 'bg-green-100', text: 'text-green-700' },
      inactive: { bg: 'bg-gray-100', text: 'text-gray-700' },
      superseded: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
      pending: { bg: 'bg-blue-100', text: 'text-blue-700' },
    };
    const badge = badges[status] || badges.active;
    const labels: Record<string, string> = {
      active: '激活',
      inactive: '已禁用',
      superseded: '已替代',
      pending: '待确认',
    };
    return (
      <span className={`text-xs px-2 py-1 rounded ${badge.bg} ${badge.text}`}>
        {labels[status] || status}
      </span>
    );
  };

  // Group memories by type
  const groupedMemories = memories.reduce((groups, memory) => {
    const type = memory.memory_type || 'other';
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(memory);
    return groups;
  }, {} as Record<string, MemoryItem[]>);

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-100">记忆中心</h1>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={autoMemoryEnabled}
                onChange={toggleAutoMemory}
                className="w-4 h-4 rounded bg-gray-700 border-gray-600"
              />
              <span>自动记忆</span>
            </label>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-400 mb-1">记忆类型</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm"
            >
              {MEMORY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-gray-400 mb-1">状态</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm"
            >
              {STATUS_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 text-sm font-medium"
            >
              + 添加记忆
            </button>
            <button
              onClick={handleDeleteAll}
              className="bg-red-500/20 text-red-400 px-4 py-2 rounded-lg hover:bg-red-500/30 text-sm"
            >
              清空全部
            </button>
          </div>
        </div>

        {showAddForm && (
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 mb-6">
            <h2 className="font-semibold text-gray-100 mb-4">添加记忆</h2>
            <form onSubmit={handleAddMemory} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">记忆类型</label>
                  <select
                    value={formData.memory_type}
                    onChange={(e) => setFormData({ ...formData, memory_type: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-200"
                  >
                    {MEMORY_TYPES.filter((t) => t.value).map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">重要度 (1-10)</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={formData.importance_score}
                    onChange={(e) => setFormData({ ...formData, importance_score: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-200"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">内容</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-200"
                  placeholder="输入要记忆的内容..."
                  required
                />
              </div>
              <div className="flex gap-2">
                <button type="submit" className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 text-sm font-medium">
                  保存
                </button>
                <button type="button" onClick={() => setShowAddForm(false)} className="bg-gray-700 text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-600 text-sm">
                  取消
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div className="text-center text-gray-500 py-8">加载中...</div>
        ) : memories.length === 0 ? (
          <div className="text-center text-gray-500 py-8">还没有记忆</div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedMemories).map(([type, mems]) => (
              <div key={type} className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-gray-750 border-b border-gray-700 flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-200">{getTypeLabel(type)}</span>
                  <span className="text-xs text-gray-500">{mems.length}条</span>
                </div>
                <div className="divide-y divide-gray-700">
                  {mems.map((mem) => (
                    <div key={mem.id} className="p-4">
                      {editingId === mem.id ? (
                        <div className="space-y-3">
                          <div className="grid md:grid-cols-2 gap-3">
                            <select
                              value={editFormData.memory_type}
                              onChange={(e) => setEditFormData({ ...editFormData, memory_type: e.target.value })}
                              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-200 text-sm"
                            >
                              {MEMORY_TYPES.filter((t) => t.value).map((t) => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                              ))}
                            </select>
                            <input
                              type="number"
                              min="1"
                              max="10"
                              value={editFormData.importance_score}
                              onChange={(e) => setEditFormData({ ...editFormData, importance_score: parseInt(e.target.value) })}
                              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-200 text-sm"
                              placeholder="重要度 1-10"
                            />
                          </div>
                          <textarea
                            value={editFormData.content}
                            onChange={(e) => setEditFormData({ ...editFormData, content: e.target.value })}
                            rows={2}
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-200 text-sm"
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleUpdateMemory(mem.id)}
                              className="bg-primary-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-primary-700"
                            >
                              保存
                            </button>
                            <button
                              onClick={handleCancelEdit}
                              className="bg-gray-700 text-gray-300 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-600"
                            >
                              取消
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              {getStatusBadge(mem.status)}
                              <span className="text-xs text-gray-500">
                                重要度: {mem.importance_score}
                              </span>
                              {(mem as any).confidence_score && (
                                <span className="text-xs text-gray-500">
                                  置信度: {(mem as any).confidence_score}
                                </span>
                              )}
                              <span className="text-xs text-gray-500">
                                {getSourceLabel(mem.source)}
                              </span>
                              <span className="text-xs text-gray-500">
                                {dayjs(mem.created_at).format('YYYY-MM-DD HH:mm')}
                              </span>
                            </div>
                            <p className="text-gray-200 whitespace-pre-wrap">{mem.content}</p>
                            {(mem as any).last_used_at && (
                              <p className="text-xs text-gray-500 mt-1">
                                最近使用: {dayjs((mem as any).last_used_at).format('YYYY-MM-DD HH:mm')}
                              </p>
                            )}
                          </div>
                          <div className="flex gap-2 flex-shrink-0">
                            <button
                              onClick={() => handleEdit(mem)}
                              className="text-blue-400 hover:text-blue-300 text-sm"
                            >
                              编辑
                            </button>
                            {mem.status === 'active' ? (
                              <button
                                onClick={() => handleDisable(mem.id)}
                                className="text-gray-400 hover:text-gray-300 text-sm"
                              >
                                禁用
                              </button>
                            ) : (
                              <button
                                onClick={() => handleEnable(mem.id)}
                                className="text-green-400 hover:text-green-300 text-sm"
                              >
                                启用
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}