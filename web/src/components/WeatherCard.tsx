/** components/WeatherCard.tsx — Displays weather data returned by the API. */
import { WeatherResponse } from '@/api/endpoints';
import bn from '@/i18n/bn';

interface Props { data: WeatherResponse }

export default function WeatherCard({ data }: Props) {
  return (
    <div className="rounded-2xl bg-gradient-to-br from-brand-50 to-brand-100 dark:from-gray-800 dark:to-gray-700 p-4 shadow-sm text-sm space-y-3">
      {/* Header: place + condition */}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold text-brand-800 dark:text-brand-300 text-base">
            {data.place}
          </p>
          <p className="text-gray-600 dark:text-gray-300">{data.condition}</p>
        </div>
        <p className="text-3xl font-bold text-brand-700 dark:text-brand-300">
          {data.temperature}°C
        </p>
      </div>

      {/* Grid of metrics */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {[
          { label: bn.humidity,  value: `${data.humidity}%` },
          { label: bn.rain,      value: `${data.rain_probability}%` },
          { label: bn.wind,      value: `${data.wind_speed} কিমি/ঘ` },
          { label: bn.uv,        value: String(data.uv_index) },
          { label: bn.rain3d,    value: `${data.rain_3day_mm} মিমি` },
          { label: bn.et0,       value: `${data.et0_3day_mm} মিমি` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white/60 dark:bg-gray-900/40 rounded-lg px-3 py-1.5">
            <p className="text-gray-500 dark:text-gray-400">{label}</p>
            <p className="font-semibold text-gray-800 dark:text-gray-200">{value}</p>
          </div>
        ))}
      </div>

      {/* Agricultural advice */}
      {data.agri_advice && (
        <div className="bg-brand-600/10 dark:bg-brand-900/30 rounded-xl px-3 py-2">
          <p className="text-xs font-semibold text-brand-700 dark:text-brand-300 mb-1">
            🌾 {bn.agriAdvice}
          </p>
          <p className="text-gray-700 dark:text-gray-300 text-xs leading-relaxed">
            {data.agri_advice}
          </p>
        </div>
      )}
    </div>
  );
}
