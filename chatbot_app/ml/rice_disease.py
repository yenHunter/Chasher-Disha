"""
rice_disease.py — YOLOv8-nano inference wrapper for rice leaf disease detection.

M4 / ML-2 — Chasher-Disha

Design principles
-----------------
* Lazy loading: the model is NOT loaded at import time.  It is loaded once on
  the first call to predict() and cached via functools.lru_cache.  This mirrors
  the BanglaBERT lazy-loading pattern from M1/PERF-1.

* No Django dependency: this module is a plain Python service layer.  The view
  in views.py imports and calls predict(); the view handles HTTP concerns.

* Graceful degradation: if the weights file is missing (before training is
  complete), a ModelNotReadyError is raised with a clear human-readable message.
  The view converts this to an HTTP 503.

Classes (6)
-----------
  0  Healthy
  1  Blast
  2  Brown Spot
  3  Leaf Smut
  4  Rice Tungro
  5  Sheath Blight

Response schema (returned by predict())
---------------------------------------
  {
    "success":    bool,
    "disease":    str,          # English class name
    "disease_bn": str,          # Bangla class name
    "confidence": float,        # 0.0 – 1.0
    "advice":     str,          # Bangla management advice
    "all_detections": [         # all boxes above threshold
      {"disease": str, "disease_bn": str, "confidence": float,
       "bbox": [x1, y1, x2, y2]}
    ]
  }
"""

from __future__ import annotations

import functools
import io
import logging
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_PATH = Path(__file__).parent / "models" / "rice_disease.pt"

# ---------------------------------------------------------------------------
# Confidence threshold — detections below this are ignored
# ---------------------------------------------------------------------------
CONF_THRESHOLD = 0.40

# ---------------------------------------------------------------------------
# Class metadata
# ---------------------------------------------------------------------------
CLASS_NAMES_EN = [
    "Healthy",
    "Blast",
    "Brown Spot",
    "Leaf Smut",
    "Rice Tungro",
    "Sheath Blight",
]

CLASS_NAMES_BN = {
    "Healthy":      "সুস্থ ধান পাতা",
    "Blast":        "ব্লাস্ট রোগ",
    "Brown Spot":   "বাদামি দাগ রোগ",
    "Leaf Smut":    "পাতার কালো দাগ রোগ",
    "Rice Tungro":  "টুংরো ভাইরাস রোগ",
    "Sheath Blight":"কান্ড পচা রোগ",
}

# Bangla management advice per class
DISEASE_ADVICE: dict[str, str] = {
    "Healthy": (
        "আপনার ধান গাছ সুস্থ আছে। নিয়মিত সেচ ও সার প্রয়োগ চালিয়ে যান।"
    ),
    "Blast": (
        "ব্লাস্ট রোগ শনাক্ত হয়েছে। ট্রাইসাইক্লাজল ৭৫% WP (৫ গ্রাম/১০ লিটার পানি) "
        "স্প্রে করুন। আক্রান্ত পাতা ও কুশি সরিয়ে ফেলুন। "
        "নাইট্রোজেন সার সাময়িকভাবে বন্ধ রাখুন।"
    ),
    "Brown Spot": (
        "বাদামি দাগ রোগ শনাক্ত হয়েছে। ম্যানকোজেব ৮০% WP (২০ গ্রাম/১০ লিটার পানি) "
        "৭ দিন অন্তর দুইবার স্প্রে করুন। "
        "মাটিতে পটাশ সার প্রয়োগ করুন।"
    ),
    "Leaf Smut": (
        "পাতার কালো দাগ (লিফ স্মাট) শনাক্ত হয়েছে। "
        "থিরাম বা কার্বেন্ডাজিম দিয়ে বীজ শোধন করুন। "
        "আক্রান্ত পাতা কেটে পুড়িয়ে ফেলুন।"
    ),
    "Rice Tungro": (
        "টুংরো ভাইরাস রোগ শনাক্ত হয়েছে — এটি সবুজ পাতাহপার দ্বারা ছড়ায়। "
        "ইমিডাক্লোপ্রিড (০.৩ মিলি/লিটার) স্প্রে করে বাহক পোকা দমন করুন। "
        "আক্রান্ত গাছ তুলে পুড়িয়ে ফেলুন। প্রতিরোধী জাত ব্যবহার করুন।"
    ),
    "Sheath Blight": (
        "কান্ড পচা (শিথ ব্লাইট) রোগ শনাক্ত হয়েছে। "
        "হেক্সাকোনাজল ৫% SC (১ মিলি/লিটার পানি) স্প্রে করুন। "
        "জমিতে পানি নিষ্কাশন নিশ্চিত করুন। গাছের ঘনত্ব কমান।"
    ),
}


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class ModelNotReadyError(Exception):
    """Raised when the trained weights file is missing."""


class InferenceError(Exception):
    """Raised when YOLO inference fails unexpectedly."""


# ---------------------------------------------------------------------------
# Lazy model loader
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _get_model():
    """
    Load and cache the YOLOv8 model.
    Called automatically on first predict() call.
    Raises ModelNotReadyError if weights are not found.
    """
    if not MODEL_PATH.exists():
        raise ModelNotReadyError(
            f"Model weights not found at {MODEL_PATH}. "
            "Train the model first: see train/README.md, "
            "or run: python scripts/download_model.py"
        )
    try:
        from ultralytics import YOLO  # noqa: PLC0415
    except ImportError as exc:
        raise ModelNotReadyError(
            "ultralytics is not installed. Run: pip install ultralytics"
        ) from exc

    logger.info("[RiceDisease] Loading model from %s …", MODEL_PATH)
    model = YOLO(str(MODEL_PATH))
    logger.info("[RiceDisease] Model loaded.")
    return model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def predict(image_bytes: bytes) -> dict:
    """
    Run YOLOv8-nano inference on a rice leaf image.

    Parameters
    ----------
    image_bytes : bytes
        Raw bytes of a JPEG/PNG image (from request.FILES["image"].read()).

    Returns
    -------
    dict
        {
          "success":    bool,
          "disease":    str,
          "disease_bn": str,
          "confidence": float,
          "advice":     str,
          "all_detections": [...]
        }

    Raises
    ------
    ModelNotReadyError
        If weights are missing or ultralytics is not installed.
    InferenceError
        If YOLO inference fails for an unexpected reason.
    ValueError
        If image_bytes cannot be decoded as an image.
    """
    # -- Decode image --------------------------------------------------------
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc

    img_np = np.array(img)

    # -- Load model (cached after first call) --------------------------------
    model = _get_model()

    # -- Run inference -------------------------------------------------------
    try:
        results = model.predict(
            source=img_np,
            conf=CONF_THRESHOLD,
            verbose=False,
        )
    except Exception as exc:
        raise InferenceError(f"YOLO inference failed: {exc}") from exc

    # -- Parse detections ----------------------------------------------------
    all_detections: list[dict] = []

    if results and results[0].boxes is not None:
        boxes  = results[0].boxes
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf   = float(boxes.conf[i].item())
            xyxy   = boxes.xyxy[i].tolist()   # [x1, y1, x2, y2]

            if cls_id < len(CLASS_NAMES_EN):
                cls_name = CLASS_NAMES_EN[cls_id]
            else:
                cls_name = f"unknown_{cls_id}"

            all_detections.append({
                "disease":    cls_name,
                "disease_bn": CLASS_NAMES_BN.get(cls_name, cls_name),
                "confidence": round(conf, 4),
                "bbox":       [round(v, 1) for v in xyxy],
            })

    # -- No detection --------------------------------------------------------
    if not all_detections:
        return {
            "success":        True,
            "disease":        "Healthy",
            "disease_bn":     CLASS_NAMES_BN["Healthy"],
            "confidence":     0.0,
            "advice":         DISEASE_ADVICE["Healthy"],
            "all_detections": [],
        }

    # -- Best detection (highest confidence) ---------------------------------
    best = max(all_detections, key=lambda d: d["confidence"])
    disease   = best["disease"]
    disease_bn = best["disease_bn"]
    confidence = best["confidence"]

    logger.info(
        "[RiceDisease] best=%s  conf=%.3f  total_boxes=%d",
        disease, confidence, len(all_detections),
    )

    return {
        "success":        True,
        "disease":        disease,
        "disease_bn":     disease_bn,
        "confidence":     confidence,
        "advice":         DISEASE_ADVICE.get(disease, ""),
        "all_detections": all_detections,
    }
