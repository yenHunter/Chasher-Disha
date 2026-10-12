"""
scripts/download_model.py — Download pre-trained rice disease weights.

M4 / ML-3 — Chasher-Disha

Usage
-----
  python scripts/download_model.py

The script downloads rice_disease.pt (and optionally rice_disease.onnx)
from a configurable source and places them at:
  chatbot_app/ml/models/rice_disease.pt
  chatbot_app/ml/models/rice_disease.onnx

Configuration
-------------
Set the environment variable(s) in your .env file:

  MODEL_DOWNLOAD_URL=https://...           # direct HTTPS link to rice_disease.pt
  MODEL_ONNX_DOWNLOAD_URL=https://...      # optional: rice_disease.onnx

If these are not set, the script prints instructions for manual placement.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

# Try to load .env so the script works standalone
try:
    import environ  # noqa: PLC0415
    env = environ.Env()
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        environ.Env.read_env(str(env_file))
except ImportError:
    pass  # django-environ not required for this script

REPO_ROOT  = Path(__file__).parent.parent
MODEL_DIR  = REPO_ROOT / "chatbot_app" / "ml" / "models"
PT_PATH    = MODEL_DIR / "rice_disease.pt"
ONNX_PATH  = MODEL_DIR / "rice_disease.onnx"


def _download(url: str, dest: Path) -> None:
    """Stream-download *url* → *dest* with a progress bar."""
    import urllib.request  # noqa: PLC0415

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}\n  → {dest}")

    def _progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            bar = "#" * (pct // 5)
            print(f"\r  [{bar:<20}] {pct:3d}%", end="", flush=True)

    urllib.request.urlretrieve(url, str(dest), reporthook=_progress)
    print()  # newline after progress bar


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    pt_url   = os.environ.get("MODEL_DOWNLOAD_URL", "").strip()
    onnx_url = os.environ.get("MODEL_ONNX_DOWNLOAD_URL", "").strip()

    if not pt_url:
        print(
            "MODEL_DOWNLOAD_URL is not set in .env\n\n"
            "Manual placement:\n"
            "  1. Train the model:  python train/train.py\n"
            "     OR download from your team's shared storage.\n"
            f"  2. Place the file at: {PT_PATH}\n"
            f"     (ONNX optional):    {ONNX_PATH}"
        )
        sys.exit(0)

    # -- Download .pt --------------------------------------------------------
    if PT_PATH.exists():
        print(f"rice_disease.pt already present at {PT_PATH}. Skipping.")
    else:
        _download(pt_url, PT_PATH)
        size_mb = PT_PATH.stat().st_size / (1024 ** 2)
        print(f"  Downloaded: {size_mb:.1f} MB")

    # -- Download .onnx (optional) -------------------------------------------
    if onnx_url:
        if ONNX_PATH.exists():
            print(f"rice_disease.onnx already present at {ONNX_PATH}. Skipping.")
        else:
            _download(onnx_url, ONNX_PATH)
            size_mb = ONNX_PATH.stat().st_size / (1024 ** 2)
            print(f"  Downloaded: {size_mb:.1f} MB")

    print("\nDone. Model weights are ready.")
    print(f"  PT   : {PT_PATH}")
    if ONNX_PATH.exists():
        print(f"  ONNX : {ONNX_PATH}")


if __name__ == "__main__":
    main()
