/** pages/FertilizerPage.tsx — Fertilizer recommendation form (FRONT-6). */
import React, { useState } from 'react';
import { apiClient } from '@/api/client';
import bn from '@/i18n/bn';

interface FertResponse {
  fertilizer:           string;
  dose_kg_per_bigha:    number;
  application_method:   string;
  timing:               string;
  warnings:             string;
}

const CROPS        = ['ধান', 'পাট', 'আলু', 'গম', 'সরিষা', 'ভুট্টা'];
const SOIL_TYPES   = ['এঁটেল', 'দোআঁশ', 'বেলে দোআঁশ', 'বেলে'];
const GROWTH_STAGES = ['চারা', 'কুশি', 'থোড়', 'ফুল', 'পাকা'];

export default function FertilizerPage() {
  const [crop,     setCrop]     = useState('ধান');
  const [soil,     setSoil]     = useState('দোআঁশ');
  const [stage,    setStage]    = useState('কুশি');
  const [symptoms, setSymptoms] = useState('');
  const [result,   setResult]   = useState<FertResponse | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await apiClient.post<FertResponse>('/fertilizer/', {
        crop, soil_type: soil, growth_stage: stage, deficiency_symptoms: symptoms,
      });
      setResult(data);
    } catch (err: unknown) {
      const d = (err as { response?: { data?: { error?: string } } })?.response?.data;
      setError(d?.error ?? 'ত্রুটি হয়েছে। আবার চেষ্টা করুন।');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-md mx-auto space-y-4">
      <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">🌱 {bn.fertilizerTitle}</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        {[
          { label: bn.crop,        value: crop,  set: setCrop,  opts: CROPS },
          { label: bn.soilType,    value: soil,  set: setSoil,  opts: SOIL_TYPES },
          { label: bn.growthStage, value: stage, set: setStage, opts: GROWTH_STAGES },
        ].map(({ label, value, set, opts }) => (
          <div key={label}>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
            <select
              value={value}
              onChange={(e) => set(e.target.value)}
              className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {opts.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        ))}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{bn.symptoms}</label>
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            rows={2}
            placeholder="যেমন: পাতা হলুদ হয়ে যাচ্ছে"
            className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        {error && <p className="text-xs text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold rounded-xl py-2.5 transition"
        >
          {loading ? bn.loading : bn.getFertAdvice}
        </button>
      </form>

      {result && (
        <div className="bg-brand-50 dark:bg-gray-800 rounded-2xl p-4 space-y-2 text-sm">
          <p className="font-semibold text-brand-700 dark:text-brand-300">🌿 {bn.fertResult}</p>
          {[
            ['সার',       result.fertilizer],
            ['মাত্রা',    `${result.dose_kg_per_bigha} কেজি/বিঘা`],
            ['প্রয়োগ',   result.application_method],
            ['সময়',      result.timing],
            ['সতর্কতা',  result.warnings],
          ].map(([k, v]) => v ? (
            <div key={k}>
              <span className="text-gray-500 dark:text-gray-400">{k}: </span>
              <span className="text-gray-800 dark:text-gray-200">{v}</span>
            </div>
          ) : null)}
        </div>
      )}
    </div>
  );
}
