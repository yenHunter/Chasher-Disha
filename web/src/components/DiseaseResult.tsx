/** components/DiseaseResult.tsx — Shows disease detection result (FRONT-5). */
import { DiseaseResponse } from '@/api/endpoints';
import bn from '@/i18n/bn';

interface Props { data: DiseaseResponse }

const DISEASE_COLOR: Record<string, string> = {
  Healthy:       'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  Blast:         'bg-red-100   text-red-800   dark:bg-red-900   dark:text-red-200',
  'Brown Spot':  'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  'Leaf Smut':   'bg-gray-100  text-gray-800  dark:bg-gray-700  dark:text-gray-200',
  'Rice Tungro': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  'Sheath Blight': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
};

export default function DiseaseResult({ data }: Props) {
  const colorClass = DISEASE_COLOR[data.disease] ?? 'bg-gray-100 text-gray-800';
  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 p-4 space-y-3 text-sm">
      {/* Badge */}
      <div className="flex items-center justify-between">
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colorClass}`}>
          {data.disease_bn}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {bn.confidence}: <strong>{data.confidence}</strong>
        </span>
      </div>
      {/* Advice */}
      {data.advice && (
        <div className="bg-brand-50 dark:bg-gray-800 rounded-xl px-3 py-2">
          <p className="text-xs font-semibold text-brand-700 dark:text-brand-300 mb-1">
            💊 {bn.advice}
          </p>
          <p className="text-gray-700 dark:text-gray-300 text-xs leading-relaxed">
            {data.advice}
          </p>
        </div>
      )}
    </div>
  );
}
