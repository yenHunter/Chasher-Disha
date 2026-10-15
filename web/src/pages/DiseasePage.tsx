/**
 * pages/DiseasePage.tsx
 * M7: OFFLINE-3 update — Tries on-device ONNX first when offline;
 * falls back to server API when online or when ONNX fails.
 */
import { useRef, useState } from 'react';
import { detectDisease, DiseaseResponse, apiErrorMessage } from '@/api/endpoints';
import { runOnnxDetection, OnnxNotReadyError, OnnxDiseaseResult } from '@/lib/onnxDisease';
import { useNetworkStore } from '@/store/networkStore';
import DiseaseResult from '@/components/DiseaseResult';
import bn from '@/i18n/bn';

// Unify server and ONNX results into the component's shared shape
function onnxToDisplay(r: OnnxDiseaseResult): DiseaseResponse {
  return {
    success:        true,
    disease:        r.disease,
    disease_bn:     r.disease_bn,
    confidence:     r.confidence,
    advice:         r.advice,
    all_detections: [],
  };
}

export default function DiseasePage() {
  const isOnline  = useNetworkStore((s) => s.isOnline);
  const [result,  setResult]  = useState<DiseaseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [source,  setSource]  = useState<'server' | 'onnx' | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setResult(null); setError(null); setSource(null);
    setLoading(true);

    try {
      if (!isOnline) {
        // OFFLINE-3: attempt on-device ONNX
        try {
          const onnxResult = await runOnnxDetection(file);
          setResult(onnxToDisplay(onnxResult));
          setSource('onnx');
        } catch (onnxErr) {
          if (onnxErr instanceof OnnxNotReadyError) {
            setError(bn.modelNotReady + ' (অফলাইন মোডে মডেল পাওয়া যায়নি।)');
          } else {
            setError(`অফলাইন শনাক্তকরণ ব্যর্থ: ${String(onnxErr)}`);
          }
        }
      } else {
        // Online: try server first, fall back to ONNX
        try {
          const serverResult = await detectDisease(file);
          setResult(serverResult);
          setSource('server');
        } catch (serverErr) {
          // Server unavailable → try ONNX fallback
          try {
            const onnxResult = await runOnnxDetection(file);
            setResult(onnxToDisplay(onnxResult));
            setSource('onnx');
          } catch {
            setError(apiErrorMessage(serverErr));
          }
        }
      }
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  }

  return (
    <div className="p-6 max-w-md mx-auto space-y-4">
      <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">🔬 {bn.diseaseTitle}</h2>

      {/* Source badge */}
      {source && (
        <p className="text-xs text-gray-400">
          {source === 'onnx' ? '📱 ডিভাইসে শনাক্ত (অফলাইন)' : '☁️ সার্ভারে শনাক্ত (অনলাইন)'}
        </p>
      )}

      {/* Upload zone */}
      <div
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-brand-300 dark:border-brand-700 rounded-2xl p-8 text-center cursor-pointer hover:bg-brand-50 dark:hover:bg-gray-800 transition"
      >
        {preview ? (
          <img src={preview} alt="preview" className="max-h-48 mx-auto rounded-xl object-contain" />
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-sm">{bn.uploadImage}</p>
        )}
      </div>
      <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleFile} />

      {loading && <p className="text-sm text-center text-gray-500">{bn.analyzing}</p>}
      {error   && <p className="text-sm text-red-500">{error}</p>}
      {result  && <DiseaseResult data={result} />}
    </div>
  );
}
