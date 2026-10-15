/**
 * lib/onnxDisease.ts
 * M7: OFFLINE-3 — On-device rice disease inference via onnxruntime-web (WASM).
 *
 * Requires rice_disease.onnx to be placed at:
 *   web/src/assets/rice_disease.onnx   (bundled into app by Vite)
 * OR at a public URL defined by VITE_ONNX_MODEL_URL env variable.
 *
 * The model is lazy-loaded once and cached in module scope.
 *
 * Preprocessing matches the training pipeline in train/train.py:
 *   - Resize to 640×640
 *   - Normalise to [0, 1] float32
 *   - NCHW layout (batch=1, channels=3, height=640, width=640)
 *
 * Class order must match train/data.yaml:
 *   0=Healthy, 1=Blast, 2=Brown Spot, 3=Leaf Smut, 4=Rice Tungro, 5=Sheath Blight
 */

import * as ort from 'onnxruntime-web';

// --- Class definitions (must match train/data.yaml) -------------------------
const CLASS_EN: string[] = [
  'Healthy', 'Blast', 'Brown Spot', 'Leaf Smut', 'Rice Tungro', 'Sheath Blight',
];
const CLASS_BN: string[] = [
  'সুস্থ গাছ', 'ব্লাস্ট রোগ', 'বাদামি দাগ রোগ', 'পাতার ঝুল', 'টুংরো রোগ', 'শিথ ব্লাইট',
];
const ADVICE: Record<string, string> = {
  'Healthy':       'গাছ সুস্থ আছে। নিয়মিত পরিচর্যা চালিয়ে যান।',
  'Blast':         'ট্রাইসাইক্লাজল (০.১%) বা ইসোপ্রোথায়োলেন ছত্রাকনাশক স্প্রে করুন। আক্রান্ত গাছের অবশিষ্ট পুড়িয়ে ফেলুন।',
  'Brown Spot':    'ম্যানকোজেব (০.২৫%) বা প্রপিকোনাজল ছত্রাকনাশক ব্যবহার করুন। পটাশ সারের পরিমাণ বাড়ান।',
  'Leaf Smut':     'কার্বেন্ডাজিম বা থিরাম ছত্রাকনাশক ব্যবহার করুন। আক্রান্ত শীষ কেটে নষ্ট করুন।',
  'Rice Tungro':   'সবুজ পাতাফড়িং দমন করুন — ইমিডাক্লোপ্রিড কীটনাশক স্প্রে করুন। আক্রান্ত গাছ উপড়ে পুড়িয়ে ফেলুন।',
  'Sheath Blight': 'ভ্যালিডামাইসিন বা হেক্সাকোনাজল ছত্রাকনাশক স্প্রে করুন। জমিতে অতিরিক্ত ইউরিয়া দেওয়া বন্ধ রাখুন।',
};

const MODEL_SIZE = 640;
const CONF_THRESHOLD = 0.40;

// --- Types ------------------------------------------------------------------
export interface OnnxDiseaseResult {
  disease:    string;
  disease_bn: string;
  confidence: string;
  advice:     string;
  source:     'onnx';
}

export class OnnxNotReadyError extends Error {}
export class OnnxInferenceError extends Error {}

// --- Model session cache ----------------------------------------------------
let _session: ort.InferenceSession | null = null;

async function getSession(): Promise<ort.InferenceSession> {
  if (_session) return _session;

  // WASM backend — works in Capacitor WebView without native code
  ort.env.wasm.numThreads = 2;

  const modelUrl =
    (import.meta.env.VITE_ONNX_MODEL_URL as string | undefined) ??
    new URL('@/assets/rice_disease.onnx', import.meta.url).href;

  try {
    _session = await ort.InferenceSession.create(modelUrl, {
      executionProviders: ['wasm'],
    });
    return _session;
  } catch (e) {
    throw new OnnxNotReadyError(
      `ONNX model not found at ${modelUrl}. ` +
      'Place rice_disease.onnx in web/src/assets/ after training.',
    );
  }
}

// --- Image preprocessing ----------------------------------------------------
async function imageToTensor(
  imageData: ImageData,
): Promise<ort.Tensor> {
  // Resize via OffscreenCanvas (Capacitor WebView supports it)
  const canvas  = new OffscreenCanvas(MODEL_SIZE, MODEL_SIZE);
  const ctx     = canvas.getContext('2d')!;
  // Draw into a temp canvas at native size first
  const tmp     = new OffscreenCanvas(imageData.width, imageData.height);
  tmp.getContext('2d')!.putImageData(imageData, 0, 0);
  const blob    = await tmp.convertToBlob();
  const bmp     = await createImageBitmap(blob);
  ctx.drawImage(bmp, 0, 0, MODEL_SIZE, MODEL_SIZE);
  const resized = ctx.getImageData(0, 0, MODEL_SIZE, MODEL_SIZE);

  // NCHW float32 [1, 3, 640, 640]
  const float32 = new Float32Array(3 * MODEL_SIZE * MODEL_SIZE);
  const d       = resized.data;
  const total   = MODEL_SIZE * MODEL_SIZE;
  for (let i = 0; i < total; i++) {
    float32[i]             = d[i * 4]     / 255;   // R
    float32[total + i]     = d[i * 4 + 1] / 255;   // G
    float32[total * 2 + i] = d[i * 4 + 2] / 255;   // B
  }
  return new ort.Tensor('float32', float32, [1, 3, MODEL_SIZE, MODEL_SIZE]);
}

// --- Post-process YOLOv8 output ---------------------------------------------
// YOLOv8 output shape: [1, 4+nc, 8400] (cx, cy, w, h, cls0..cls_n−1)
function parseDetections(
  output: ort.Tensor,
  nc: number,
): Array<{ classIdx: number; confidence: number }> {
  const data   = output.data as Float32Array;
  const rows   = 8400;

  const results: Array<{ classIdx: number; confidence: number }> = [];

  for (let i = 0; i < rows; i++) {
    // YOLOv8 output is stored column-major: index = col * rows + row
    const classScores = Array.from(
      { length: nc },
      (_, c) => (data as Float32Array)[(4 + c) * rows + i],
    );
    const maxScore = Math.max(...classScores);
    if (maxScore >= CONF_THRESHOLD) {
      results.push({ classIdx: classScores.indexOf(maxScore), confidence: maxScore });
    }
  }
  return results;
}

// --- Public API -------------------------------------------------------------
export async function runOnnxDetection(file: File): Promise<OnnxDiseaseResult> {
  // Decode file to ImageData
  const bitmap = await createImageBitmap(file);
  const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0);
  const imageData = canvas.getContext('2d')!.getImageData(0, 0, bitmap.width, bitmap.height);

  let session: ort.InferenceSession;
  try {
    session = await getSession();
  } catch (e) {
    if (e instanceof OnnxNotReadyError) throw e;
    throw new OnnxInferenceError(String(e));
  }

  const tensor  = await imageToTensor(imageData);
  const feeds   = { images: tensor };
  let   results: ort.InferenceSession.OnnxValueMapType;

  try {
    results = await session.run(feeds);
  } catch (e) {
    throw new OnnxInferenceError(`Inference failed: ${String(e)}`);
  }

  const outputKey  = Object.keys(results)[0];
  const detections = parseDetections(results[outputKey], CLASS_EN.length);

  if (detections.length === 0) {
    return {
      disease:    'Healthy',
      disease_bn: CLASS_BN[0],
      confidence: '—',
      advice:     ADVICE['Healthy'],
      source:     'onnx',
    };
  }

  // Pick highest confidence detection
  detections.sort((a, b) => b.confidence - a.confidence);
  const best = detections[0];
  const name = CLASS_EN[best.classIdx] ?? 'Unknown';

  return {
    disease:    name,
    disease_bn: CLASS_BN[best.classIdx] ?? name,
    confidence: `${(best.confidence * 100).toFixed(1)}%`,
    advice:     ADVICE[name] ?? '',
    source:     'onnx',
  };
}
