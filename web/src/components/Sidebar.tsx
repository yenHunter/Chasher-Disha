/** components/Sidebar.tsx — Left side-menu (FRONT-4). */
import { useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import { useAuthStore }  from '@/store/authStore';
import { clearHistory }  from '@/api/endpoints';
import bn from '@/i18n/bn';

interface Props { onNavigate: (page: 'chat' | 'disease' | 'fertilizer' | 'weather') => void; }

export default function Sidebar({ onNavigate }: Props) {
  const { clearMessages, exportTxt, darkMode, setDarkMode, sessionLabel, setSessionLabel } = useChatStore();
  const { clearAuth } = useAuthStore();
  const [editLabel, setEditLabel] = useState(false);
  const [labelDraft, setLabelDraft] = useState(sessionLabel);

  async function handleClearChat() {
    clearMessages();
    try { await clearHistory(); } catch { /* non-fatal */ }
  }

  function handleEndSession() {
    clearMessages();
    clearAuth();
  }

  function handleLabelSave() {
    setSessionLabel(labelDraft.trim() || 'চ্যাট ১');
    setEditLabel(false);
  }

  return (
    <aside className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
        <h1 className="text-lg font-bold text-brand-700 dark:text-brand-400">🌾 {bn.appName}</h1>
        <p className="text-xs text-gray-500 dark:text-gray-400">{bn.appTagline}</p>
      </div>

      {/* Session label (editable) */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        {editLabel ? (
          <div className="flex gap-1">
            <input
              autoFocus
              value={labelDraft}
              onChange={(e) => setLabelDraft(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLabelSave()}
              className="flex-1 text-sm border border-brand-400 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none"
            />
            <button onClick={handleLabelSave} className="text-brand-600 text-xs font-semibold">✓</button>
          </div>
        ) : (
          <button onClick={() => setEditLabel(true)} className="text-sm text-gray-700 dark:text-gray-300 hover:text-brand-600 dark:hover:text-brand-400 text-left truncate w-full">
            ✏️ {sessionLabel}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1">
        {([
          { key: 'chat',       icon: '💬', label: 'চ্যাট' },
          { key: 'weather',    icon: '🌦️', label: bn.weatherTitle },
          { key: 'disease',    icon: '🔬', label: bn.diseaseTitle },
          { key: 'fertilizer', icon: '🌱', label: bn.fertilizerTitle },
        ] as const).map(({ key, icon, label }) => (
          <button
            key={key}
            onClick={() => onNavigate(key)}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-gray-700 dark:text-gray-300 hover:bg-brand-50 dark:hover:bg-gray-800 transition"
          >
            <span>{icon}</span> {label}
          </button>
        ))}
      </nav>

      {/* Actions */}
      <div className="px-3 py-3 border-t border-gray-200 dark:border-gray-700 space-y-1">
        <button onClick={exportTxt} className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition">
          📥 {bn.exportChat}
        </button>
        <button onClick={handleClearChat} className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition">
          🗑️ {bn.clearChat}
        </button>
        {/* Dark mode toggle (FRONT-7) */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
        >
          {darkMode ? '☀️' : '🌙'} {darkMode ? bn.lightMode : bn.darkMode}
        </button>
        <button onClick={handleEndSession} className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition">
          🚪 {bn.endSession}
        </button>
      </div>
    </aside>
  );
}
