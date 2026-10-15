/** pages/LoginPage.tsx — JWT login form. */
import React, { useState } from 'react';
import { obtainToken, apiErrorMessage } from '@/api/endpoints';
import { useAuthStore } from '@/store/authStore';
import bn from '@/i18n/bn';

export default function LoginPage() {
  const setTokens = useAuthStore((s) => s.setTokens);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await obtainToken(username, password);
      setTokens(tokens.access, tokens.refresh, username);
    } catch (err) {
      setError(bn.loginFailed + ' (' + apiErrorMessage(err) + ')');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-50 dark:bg-gray-900 px-4">
      <div className="w-full max-w-sm bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-brand-700 dark:text-brand-400">🌾 {bn.appName}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{bn.appTagline}</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {bn.username}
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {bn.password}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 text-gray-900 dark:text-gray-100"
            />
          </div>
          {error && (
            <p className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold rounded-xl py-2.5 transition"
          >
            {loading ? bn.loading : bn.login}
          </button>
        </form>
      </div>
    </div>
  );
}
