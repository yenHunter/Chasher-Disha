/**
 * api/endpoints.ts — Typed wrappers for every REST endpoint.
 */
import { apiClient } from './client';
import axios from 'axios';

// ---------- Auth ------------------------------------------------------------
export interface TokenResponse {
  access: string;
  refresh: string;
}

export async function obtainToken(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/token/', {
    username,
    password,
  });
  return data;
}

// ---------- Chat ------------------------------------------------------------
export interface ChatResponse {
  response: string;
  sentinel?: string;
}

export async function sendChat(message: string): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>('/chat/', { message });
  return data;
}

// ---------- Weather ---------------------------------------------------------
export interface WeatherResponse {
  weather: string;
  agri_advice: string;
  place: string;
  condition: string;
  temperature: number;
  humidity: number;
  rain_probability: number;
  wind_speed: number;
  uv_index: number;
  rain_3day_mm: number;
  et0_3day_mm: number;
}

export async function fetchWeather(
  latitude: number,
  longitude: number,
): Promise<WeatherResponse> {
  const { data } = await apiClient.post<WeatherResponse>('/weather/', {
    latitude,
    longitude,
  });
  return data;
}

// ---------- Disease ---------------------------------------------------------
export interface DetectionBox {
  disease: string;
  disease_bn: string;
  confidence: number;
  bbox: [number, number, number, number];
}

export interface DiseaseResponse {
  success: boolean;
  disease: string;
  disease_bn: string;
  confidence: string;
  advice: string;
  all_detections: DetectionBox[];
}

export async function detectDisease(file: File): Promise<DiseaseResponse> {
  const form = new FormData();
  form.append('image', file);
  const { data } = await apiClient.post<DiseaseResponse>('/disease/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

// ---------- History ---------------------------------------------------------
export interface HistoryMessage {
  id: number;
  sender: 'user' | 'bot';
  text: string;
  intent: string;
  confidence: number | null;
  created_at: string;
}

export interface HistoryResponse {
  count: number;
  messages: HistoryMessage[];
}

export async function fetchHistory(
  limit = 50,
  offset = 0,
): Promise<HistoryResponse> {
  const { data } = await apiClient.get<HistoryResponse>('/history/', {
    params: { limit, offset },
  });
  return data;
}

export async function clearHistory(): Promise<void> {
  await apiClient.delete('/history/');
}

// ---------- Error helper ----------------------------------------------------
export function apiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const d = err.response?.data as Record<string, unknown> | undefined;
    return (d?.error as string) ?? (d?.detail as string) ?? err.message;
  }
  return String(err);
}
