/**
 * lib/weatherCache.ts
 * M7: OFFLINE-2 — Cache last weather response with 6-hour TTL.
 *
 * Uses capacitorBridge prefGet/prefSet so it works on both web and Android.
 */

import { prefGet, prefSet } from './capacitorBridge';
import type { WeatherResponse } from '@/api/endpoints';

const KEY_DATA = 'weather_cache_data';
const KEY_TIME = 'weather_cache_ts';
const TTL_MS   = 6 * 60 * 60 * 1000;   // 6 hours

export interface CachedWeather {
  data:         WeatherResponse;
  cachedAtMs:   number;
  /** Age label in Bangla, e.g. "শেষ আপডেট: ৩ ঘণ্টা আগে" */
  ageLabel:     string;
  isStale:      boolean;              // true if TTL exceeded but returned anyway
}

function banglaHours(ms: number): string {
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  if (h === 0) return `${m} মিনিট`;
  return `${h} ঘণ্টা${m > 0 ? ` ${m} মিনিট` : ''}`;
}

export async function saveWeatherCache(data: WeatherResponse): Promise<void> {
  await prefSet(KEY_DATA, JSON.stringify(data));
  await prefSet(KEY_TIME, String(Date.now()));
}

export async function loadWeatherCache(): Promise<CachedWeather | null> {
  const raw = await prefGet(KEY_DATA);
  const tsRaw = await prefGet(KEY_TIME);
  if (!raw || !tsRaw) return null;

  const cachedAtMs = parseInt(tsRaw, 10);
  const ageMs      = Date.now() - cachedAtMs;
  const data       = JSON.parse(raw) as WeatherResponse;

  return {
    data,
    cachedAtMs,
    ageLabel: `শেষ আপডেট: ${banglaHours(ageMs)} আগে`,
    isStale:  ageMs > TTL_MS,
  };
}
