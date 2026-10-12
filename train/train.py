"""
train.py — YOLOv8-nano training script for RiceLeafDiseaseBD.

M4 / ML-1 — Chasher-Disha

Usage
-----
  # From inside the train/ directory:
  python train.py

  # Dry-run (checks config only, no training):
  python train.py --dry-run

  # Specify a different YAML or GPU:
  python train.py --data data.yaml --device 0

Requirements
------------
  pip install -r requirements_train.txt

Dataset
-------
  Primary: RiceLeafDiseaseBD v3
    https://data.mendeley.com/datasets/86s4jzj2m4/3
  Supplementary / validation: BanglaRiceLeaf
    https://doi.org/10.7910/DVN/XAOBYW

  Download the dataset and update `data.yaml` → `path` before running.

Output
------
  runs/train/rice_disease_v1/
    weights/
      best.pt        ← copy this to chatbot_app/ml/models/rice_disease.pt
      last.pt
    results.csv      ← mAP, precision, recall per epoch
    confusion_matrix.png
    PR_curve.png
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_YAML    = Path(__file__).parent / "data.yaml"
MODEL_BASE   = "yolov8n.pt"          # nano ~3.2 MB pretrained weights
EPOCHS       = 100
IMG_SIZE     = 640
BATCH_SIZE   = 16
PATIENCE     = 20                    # early stopping: stop if no mAP gain for N epochs
DEVICE       = "cuda"                # "cuda" | "cpu" | "0,1" for multi-GPU
PROJECT_DIR  = Path(__file__).parent / "runs" / "train"
RUN_NAME     = "rice_disease_v1"

# Where to copy the best weights for the Django server
SERVER_WEIGHTS = (
    Path(__file__).parent.parent
    / "chatbot_app" / "ml" / "models" / "rice_disease.pt"
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv8-nano on RiceLeafDiseaseBD")
    parser.add_argument("--data",     default=str(DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--device",   default=DEVICE,          help="cuda | cpu | 0,1 ...")
    parser.add_argument("--epochs",   default=EPOCHS,   type=int)
    parser.add_argument("--batch",    default=BATCH_SIZE, type=int)
    parser.add_argument("--dry-run",  action="store_true",
                        help="Validate config and exit without training")
    args = parser.parse_args()

    # -- Dependency check ----------------------------------------------------
    try:
        from ultralytics import YOLO  # noqa: PLC0415
    except ImportError:
        print("ERROR: ultralytics not installed. Run:\n  pip install -r requirements_train.txt")
        sys.exit(1)

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: data.yaml not found at {data_path}")
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] Config OK — data={data_path}, device={args.device}, "
              f"epochs={args.epochs}, batch={args.batch}")
        print("[dry-run] Exiting without training.")
        return

    # -- Training ------------------------------------------------------------
    print(f"[train] Loading base model: {MODEL_BASE}")
    model = YOLO(MODEL_BASE)

    print(f"[train] Starting training — {args.epochs} epochs, img={IMG_SIZE}, "
          f"batch={args.batch}, device={args.device}")
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=IMG_SIZE,
        batch=args.batch,
        patience=PATIENCE,
        device=args.device,
        project=str(PROJECT_DIR),
        name=RUN_NAME,
        # Augmentation — good defaults for field photos
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        flipud=0.3,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.0,
    )

    best_weights = PROJECT_DIR / RUN_NAME / "weights" / "best.pt"
    if not best_weights.exists():
        print("[train] WARNING: best.pt not found — check training output.")
        return

    # -- ONNX export for mobile (OFFLINE-3) ----------------------------------
    print("[train] Exporting to ONNX (for Capacitor/WASM inference)…")
    model_best = YOLO(str(best_weights))
    model_best.export(format="onnx", imgsz=IMG_SIZE, simplify=True)
    onnx_path = best_weights.with_suffix(".onnx")

    # -- Copy weights to server path (ML-3) ----------------------------------
    SERVER_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_weights, SERVER_WEIGHTS)
    onnx_dest = SERVER_WEIGHTS.with_suffix(".onnx")
    if onnx_path.exists():
        shutil.copy2(onnx_path, onnx_dest)

    # -- Final summary -------------------------------------------------------
    metrics = results.results_dict
    map50   = metrics.get("metrics/mAP50(B)", "N/A")
    map5095 = metrics.get("metrics/mAP50-95(B)", "N/A")
    print("\n" + "=" * 60)
    print("Training complete")
    print(f"  mAP@0.5      : {map50}")
    print(f"  mAP@0.5:0.95 : {map5095}")
    print(f"  Best weights → {SERVER_WEIGHTS}")
    if onnx_path.exists():
        print(f"  ONNX model   → {onnx_dest}")
    print("=" * 60)

    target = float(map50) if isinstance(map50, (int, float)) else 0.0
    if target < 0.80:
        print(f"\nWARNING: mAP@0.5 = {map50:.3f} < 0.80 target.")
        print("  Try: more epochs, larger batch, or add augmentation.")
    else:
        print(f"\nTarget met: mAP@0.5 = {map50:.3f} ≥ 0.80 ✓")


if __name__ == "__main__":
    main()
