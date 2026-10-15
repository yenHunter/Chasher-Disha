/**
 * hooks/useWeather.ts
 * M7: OFFLINE-2 update — Returns cached weather when offline; saves to cache when online.
 */
import { useState } from 'react';
import { fetchWeather, WeatherResponse, apiErrorMessage } from '@/api/endpoints';
import { getCurrentPosition } from '@/lib/capacitorBridge';
import { saveWeatherCache, loadWeatherCache } from '@/lib/weatherCache';
import { useNetworkStore } from '@/store/networkStore';

export interface WeatherState {
  data:       WeatherResponse | null;
  ageLabel:   string | null;   // non-null when data is from cache
  loading:    boolean;
  error:      string | null;
}

export function useWeather() {
  const isOnline = useNetworkStore((s) => s.isOnline);
  const [state, setState] = useState<WeatherState>({
    data: null, ageLabel: null, loading: false, error: null,
  });

  async function load(lat?: number, lon?: number) {
    setState((s) => ({ ...s, loading: true, error: null }));

    // --- Offline path: serve from cache (OFFLINE-2) -------------------------
    if (!isOnline) {
      const cached = await loadWeatherCache();
      if (cached) {
        setState({ data: cached.data, ageLabel: cached.ageLabel, loading: false, error: null });
      } else {
        setState({
          data: null, ageLabel: null, loading: false,
          error: 'ইন্টারনেট সংযোগ নেই এবং কোনো সংরক্ষিত আবহাওয়া তথ্য নেই।',
        });
      }
      return;
    }

    // --- Online path --------------------------------------------------------
    try {
      let la = lat, lo = lon;
      if (la === undefined || lo === undefined) {
        const pos = await getCurrentPosition();
        la = pos.latitude;
        lo = pos.longitude;
      }
      const data = await fetchWeather(la, lo);
      await saveWeatherCache(data);          // persist for offline use
      setState({ data, ageLabel: null, loading: false, error: null });
    } catch (err) {
      // If online fetch fails, try cache as last resort
      const cached = await loadWeatherCache();
      if (cached) {
        setState({ data: cached.data, ageLabel: cached.ageLabel + ' (ফেচ ব্যর্থ)', loading: false, error: null });
      } else {
        setState({ data: null, ageLabel: null, loading: false, error: apiErrorMessage(err) });
      }
    }
  }

  return { ...state, load };
}
