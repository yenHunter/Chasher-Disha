/** pages/WeatherPage.tsx — Standalone weather page. */
import { useWeather } from '@/hooks/useWeather';
import WeatherCard   from '@/components/WeatherCard';
import bn from '@/i18n/bn';

export default function WeatherPage() {
  const { data, loading, error, load } = useWeather();
  return (
    <div className="p-6 max-w-md mx-auto space-y-4">
      <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">🌦️ {bn.weatherTitle}</h2>
      <button
        onClick={() => load()}
        disabled={loading}
        className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold rounded-xl py-2.5 transition"
      >
        {loading ? bn.locating : bn.weatherBtn}
      </button>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {data && <WeatherCard data={data} />}
    </div>
  );
}
