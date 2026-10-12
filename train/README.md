# train/README.md — Model Training Guide

## Overview

This directory contains everything needed to train the YOLOv8-nano rice disease detection model used by Chasher-Disha (M4 / ML-1).

**Model:** YOLOv8-nano (ultralytics)  
**Dataset:** RiceLeafDiseaseBD v3 — 9,769 images, 6 classes, collected in Gazipur, Bangladesh  
**Target:** mAP@0.5 ≥ 0.80  
**Output:** `chatbot_app/ml/models/rice_disease.pt` + `rice_disease.onnx`

---

## Step 1 — Set up the training environment

Training requires a GPU (Google Colab free tier works fine). Do **not** install training dependencies in the Django `env/` — use a separate environment or Colab.

```bash
# Local (with GPU)
python -m venv train_env
train_env\Scripts\activate          # Windows
pip install -r train/requirements_train.txt
```

---

## Step 2 — Download the dataset

### Primary dataset — RiceLeafDiseaseBD v3

1. Visit: <https://data.mendeley.com/datasets/86s4jzj2m4/3>
2. Click **Download All** (5.25 GB ZIP)
3. Extract to a folder outside the repo (e.g. `D:\datasets\RiceLeafDiseaseBD\`)
4. Expected structure:
   ```
   RiceLeafDiseaseBD/
     images/
       train/
       val/
       test/
     labels/
       train/
       val/
       test/
   ```
   > If the ZIP ships as a flat folder without `train/val/test` splits, use `split-folders`:
   > ```bash
   > pip install split-folders
   > python -c "
   > import splitfolders
   > splitfolders.ratio('RiceLeafDiseaseBD/images', output='RiceLeafDiseaseBD_split',
   >                    seed=42, ratio=(0.8, 0.1, 0.1))
   > "
   > ```

### Supplementary — BanglaRiceLeaf (Harvard Dataverse)

- DOI: <https://doi.org/10.7910/DVN/XAOBYW>
- 3 classes (subset of the 6 above). Use for additional validation only.

---

## Step 3 — Update `data.yaml`

Edit `train/data.yaml` and set `path` to the absolute path of your dataset:

```yaml
path: D:/datasets/RiceLeafDiseaseBD   # ← change this
```

---

## Step 4 — Train

```bash
cd C:\Personal Development\Chasher-Disha
python train/train.py
```

Training takes **~2–4 hours on a T4 GPU (Colab)** or longer on CPU.

### Google Colab (recommended for free GPU)

Open `train/colab_train.ipynb` in Colab, mount your Drive, and run all cells.

### Options

```bash
python train/train.py --epochs 150 --batch 32 --device 0   # larger run
python train/train.py --dry-run                             # config check only
```

---

## Step 5 — Check the results

After training, check:

```
train/runs/train/rice_disease_v1/
  results.csv             ← mAP per epoch
  confusion_matrix.png    ← per-class accuracy
  PR_curve.png
  weights/best.pt         ← auto-copied to chatbot_app/ml/models/
```

**Acceptance criterion:** `mAP50` column in `results.csv` must reach ≥ 0.80.

---

## Step 6 — Copy weights to the server

`train.py` does this automatically. To do it manually:

```bash
copy train\runs\train\rice_disease_v1\weights\best.pt chatbot_app\ml\models\rice_disease.pt
copy train\runs\train\rice_disease_v1\weights\best.onnx chatbot_app\ml\models\rice_disease.onnx
```

> **Note:** `*.pt` and `*.onnx` files are in `.gitignore`. Use `scripts/download_model.py` to distribute them.

---

## Dataset attribution

```
Primary:
  M. A. Bari et al., "RiceLeafDiseaseBD: A Comprehensive Dataset for Rice
  Leaf Disease Detection in Bangladesh", Mendeley Data, v3, 2025.
  https://data.mendeley.com/datasets/86s4jzj2m4/3

Supplementary:
  S. Ahmed et al., "BanglaRiceLeaf", Harvard Dataverse, 2023.
  https://doi.org/10.7910/DVN/XAOBYW
```
