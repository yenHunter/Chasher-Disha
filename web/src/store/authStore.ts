/**
 * store/authStore.ts — Zustand auth store (persisted to localStorage).
 * FRONT-4: End Session clears this store.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken:  string | null;
  refreshToken: string | null;
  username:     string | null;
  isAuthenticated: boolean;
  setTokens: (access: string, refresh: string, username: string) => void;
  clearAuth:  () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken:     null,
      refreshToken:    null,
      username:        null,
      isAuthenticated: false,
      setTokens: (access, refresh, username) =>
        set({ accessToken: access, refreshToken: refresh, username, isAuthenticated: true }),
      clearAuth: () =>
        set({ accessToken: null, refreshToken: null, username: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' },
  ),
);
