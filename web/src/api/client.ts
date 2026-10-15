/**
 * api/client.ts — Axios instance with JWT auth interceptor.
 *
 * - Reads access token from Zustand auth store (localStorage-persisted).
 * - On 401: attempts a silent token refresh, then retries the original request.
 * - On refresh failure: clears auth state and redirects to login.
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
});

// --- Request interceptor: attach Bearer token --------------------------------
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const raw = localStorage.getItem('auth-storage');
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as { state?: { accessToken?: string } };
        const token = parsed?.state?.accessToken;
        if (token) config.headers.Authorization = `Bearer ${token}`;
      } catch {
        // ignore parse error
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// --- Response interceptor: silent token refresh on 401 ----------------------
let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  pendingQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`;
        return apiClient(original);
      });
    }
    original._retry = true;
    isRefreshing = true;
    const raw = localStorage.getItem('auth-storage');
    const refreshToken = raw
      ? (JSON.parse(raw) as { state?: { refreshToken?: string } })?.state?.refreshToken
      : null;

    if (!refreshToken) {
      localStorage.removeItem('auth-storage');
      window.location.href = '/login';
      return Promise.reject(error);
    }
    try {
      const { data } = await axios.post<{ access: string }>(
        `${BASE_URL}/auth/token/refresh/`,
        { refresh: refreshToken },
      );
      const newAccess = data.access;
      // Patch the stored token
      const stored = JSON.parse(raw!) as { state: { accessToken: string } };
      stored.state.accessToken = newAccess;
      localStorage.setItem('auth-storage', JSON.stringify(stored));
      processQueue(null, newAccess);
      original.headers.Authorization = `Bearer ${newAccess}`;
      return apiClient(original);
    } catch (refreshError) {
      processQueue(refreshError, null);
      localStorage.removeItem('auth-storage');
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);
