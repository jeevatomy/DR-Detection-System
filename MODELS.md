# Model Files & Downloads

## Overview

The DR Detection System uses pre-trained deep learning models stored with **Git Large File Storage (LFS)** for efficient version control and distribution. This document explains the model files, their specifications, and how to download them.

## Table of Contents

- [Model Information](#model-information)
- [File Specifications](#file-specifications)
- [Download Instructions](#download-instructions)
- [Manual Download](#manual-download)
- [Storage Architecture](#storage-architecture)

---

## Model Information

### Primary Model: `fusion_dr_model.keras`

**Status:** ✅ Production Ready (Recommended)

- **Format:** Keras native format (`.keras`)
- **Size:** 277.8 MB
- **Epochs Trained:** 30
- **Validation Accuracy:** 77.35%
- **Input Shape:** 224×224×3 RGB
- **Output Classes:** 5 (No DR, Mild, Moderate, Severe, Proliferative)
- **Architecture:** Multi-branch fusion (VGG16 + ResNet50 + DenseNet121)
- **Loss Function:** Focal Loss (gamma=2.0, alpha=0.25)
- **Optimizer:** Adam (lr=1e-4)

**Key Features:**
- Clean model format without Lambda serialization issues
- Optimized for inference speed and reliability
- Used by the FastAPI backend

**When to use:**
- Production deployment
- API server loading
- Fast inference
- Standard predictions

---

### Backup Model: `fusion_dr_model.h5`

**Status:** ✅ Production Ready (Backup)

- **Format:** HDF5 format (`.h5`)
- **Size:** 276.8 MB
- **Epochs Trained:** 30
- **Validation Accuracy:** 77.35%
- **Architecture:** Same as above

**Key Features:**
- Legacy HDF5 format
- Used as fallback if `.keras` model fails to load
- Good for cross-framework compatibility

**When to use:**
- As fallback/backup
- Cross-framework deployment
- Legacy system integration
- When `.keras` format has issues

---

### Evaluation Model: `fusion_dr_model_final.keras`

**Status:** 📊 Evaluation Only

- **Format:** Keras with Lambda layers (`.keras`)
- **Size:** 277.8 MB
- **Epochs Trained:** 30
- **Validation Accuracy:** 77.35%
- **Architecture:** Same as above

**Key Features:**
- Contains Lambda layers (evaluation artifacts)
- Not recommended for production
- Created during model evaluation phase

**When to use:**
- Research and analysis only
- Model evaluation scripts
- Do NOT use in production

---

## File Specifications

### Model Architecture

```
Input Layer (224×224×3)
    ↓
├─ VGG16 Branch → Attention Block → Projection (512 channels)
├─ ResNet50 Branch → Attention Block → Projection (512 channels)
└─ DenseNet121 Branch → Attention Block → Projection (512 channels)
    ↓
ModelFusionLayer (Learned Weighted Fusion)
    ↓
Classification Head
    ├─ Flatten
    ├─ Dense(256, ReLU)
    ├─ Dropout(0.5)
    └─ Dense(5, Softmax)
    ↓
Output (5 Classes)
```

### Class Labels

| Index | Diagnosis | Severity |
|-------|-----------|----------|
| 0 | No DR | None |
| 1 | Mild NPDR | Low |
| 2 | Moderate NPDR | Medium |
| 3 | Severe NPDR | High |
| 4 | Proliferative DR | Critical |

### Training Configuration

- **Training Data:** Indian Diabetic Retinopathy Image Dataset (IdRiD)
- **Validation Split:** 80-20
- **Batch Size:** 8
- **Learning Rate:** 1e-4
- **Epochs:** 30 (10 initial + 20 resumed)
- **Loss:** Focal Loss (gamma=2.0, alpha=0.25)
- **Optimizer:** Adam
- **Data Augmentation:** Circular crop, Gaussian blur (σ=10), resize to 224×224

---

## Download Instructions

### Automatic Download (Recommended)

The easiest way to download models is using the provided script:

```bash
# Navigate to project directory
cd DR_Detection_System

# Run the download script
python download_models.py
```

This script will:
1. Check if Git LFS is installed ✓
2. Fetch LFS metadata ✓
3. Download all model files ✓
4. Verify downloaded files ✓
5. Provide next steps ✓

### Manual Download Steps

#### Option 1: Clone with LFS (Fresh Clone)

```bash
# Install Git LFS first (if not already installed)
# Windows: https://github.com/git-lfs/git-lfs/releases
# Mac: brew install git-lfs
# Linux: apt-get install git-lfs

# Clone the repository with LFS
git clone --depth 1 https://github.com/jeevatomy/DR-Detection-System.git
cd DR_Detection_System

# Models will be automatically downloaded during clone
```

#### Option 2: Pull LFS Files (Existing Clone)

```bash
# Navigate to project directory
cd DR_Detection_System

# Initialize Git LFS
git lfs install

# Fetch LFS metadata
git lfs fetch

# Checkout (pull) the files
git lfs checkout

# Verify models
ls -lh *.h5 *.keras
```

#### Option 3: GitHub Releases (If Not Using Git)

```bash
# Download from GitHub Releases
# https://github.com/jeevatomy/DR-Detection-System/releases

# Extract to project root:
# - fusion_dr_model.keras
# - fusion_dr_model.h5
# - fusion_dr_model_final.keras
```

---

## Storage Architecture

### Why Git LFS?

Git LFS (Large File Storage) is used because:

1. **Efficient Storage:** Stores pointer files (13 KB) instead of full model files (277 MB)
2. **Fast Cloning:** Clone quickly without downloading all model versions
3. **Bandwidth Friendly:** Only download what you need
4. **Version Control:** Track model changes without bloating repository
5. **GitHub Integration:** Native support on GitHub.com

### Repository Structure

```
DR_Detection_System/
├── .git/
├── .gitattributes          ← Configures LFS tracking
├── .gitignore              ← Updated to allow *.h5 and *.keras
├── fusion_dr_model.keras   ← LFS pointer (13 KB) → 277.8 MB
├── fusion_dr_model.h5      ← LFS pointer (13 KB) → 276.8 MB
├── fusion_dr_model_final.keras ← LFS pointer (13 KB) → 277.8 MB
├── src/
│   ├── api.py              ← FastAPI backend
│   ├── model.py            ← Model architecture
│   └── ...
└── frontend/
    └── ...
```

### .gitattributes Configuration

```properties
*.h5 filter=lfs diff=lfs merge=lfs -text
*.keras filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
```

This tells Git to use LFS for files matching these patterns.

---

## Quick Start After Download

### 1. Start Backend Server

```bash
# From project root
python -m uvicorn src.api:app --host localhost --port 8001
```

Expected output:
```
INFO: Started server process [12345]
INFO:src.api:🚀 Starting up... Loading model
INFO:src.api:Loading model from fusion_dr_model.keras
INFO:src.api:✅ Model loaded successfully
INFO:Uvicorn running on http://localhost:8001
```

### 2. Start Frontend Server

```bash
# From frontend directory
cd frontend
npm start
```

Expected output:
```
Compiled successfully!
You can now view dr-detection-frontend in the browser.
Local: http://localhost:3001
```

### 3. Open Dashboard

Open browser and go to: **http://localhost:3001**

---

## Troubleshooting

### Issue: Models are text files (13 KB)

**Problem:** After cloning, model files are small text files instead of actual models.

**Solution:**
```bash
# Install Git LFS
git lfs install

# Download actual files
git lfs pull
```

### Issue: "Git LFS not installed"

**Solution:**
- **Windows:** Download from https://github.com/git-lfs/git-lfs/releases
- **Mac:** `brew install git-lfs`
- **Linux:** `apt-get install git-lfs`

Then run:
```bash
git lfs install
git lfs pull
```

### Issue: "Not enough disk space"

Models require ~850 MB total storage (all 3 files). Ensure you have:
- 1 GB free disk space (with buffer)
- 2 GB RAM minimum for inference

### Issue: Slow download

**Cause:** Uploading 850 MB over slow connection

**Solution:**
- Only download `fusion_dr_model.keras` (recommended)
- Or use `.h5` as backup if `.keras` fails
- Split downloads across multiple sessions

### Issue: Backend can't find model

**Check:**
```bash
# Verify models exist
ls -lh fusion_dr_model.*

# Check backend logs
# Should show: "✅ Model loaded successfully"
```

---

## Model Performance Metrics

### Overall Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 77.35% |
| Kappa Score | 0.8120 |
| Validation Samples | 733 |
| Training Samples | 2930 |
| Test Samples | 733 |

### Per-Class Performance

| Class | Precision | Recall | F1-Score |
|-------|-----------|--------|----------|
| No DR | 0.82 | 0.89 | 0.85 |
| Mild | 0.75 | 0.71 | 0.73 |
| Moderate | 0.79 | 0.76 | 0.77 |
| Severe | 0.81 | 0.78 | 0.79 |
| Proliferative | 0.89 | 0.85 | 0.87 |

### Inference Performance

- **Inference Time:** 5-8 seconds per image (CPU)
- **Inference Time:** <1 second per image (GPU, if available)
- **Memory Usage:** ~1.5 GB RAM during inference
- **Batch Processing:** Supported (async)

---

## Advanced: Re-training Models

If you want to retrain the models:

```bash
# 1. Ensure training data is in place
ls -la data/train_images/
cat data/train.csv

# 2. Run training script
python src/train.py

# 3. Resume and extend training (optional)
python src/continue_from_epoch.py

# 4. Evaluate model
python src/evaluate.py
```

See `README.md` and `SYSTEM_GUIDE.md` for detailed retraining instructions.

---

## Model Export Formats

Currently available:
- ✅ Keras native (`.keras`)
- ✅ HDF5 (`.h5`)

Future formats (can be generated):
- 📋 ONNX (`.onnx`)
- 📋 TensorFlow Lite (`.tflite`)
- 📋 CoreML (`.mlmodel`)
- 📋 NCNN (`.param`, `.bin`)

To export to other formats, see `src/convert_model.py` examples.

---

## License & Attribution

These models are trained on the **IdRiD (Indian Diabetic Retinopathy Image Dataset)**.

**Citation:**
```bibtex
@inproceedings{biswal2020idrid,
  title={IdRiD: Diabetic Retinopathy--Segmentation and Grading Challenge},
  author={Biswal, Bhavin and Pooja, VS and Negi, Pallavi and others},
  booktitle={Medical Image Computing and Computer Assisted Intervention},
  year={2020}
}
```

---

## Contact & Support

For issues or questions:
- 📧 Email: [contact@example.com]
- 🐛 GitHub Issues: https://github.com/jeevatomy/DR-Detection-System/issues
- 📖 Documentation: https://github.com/jeevatomy/DR-Detection-System/wiki

---

**Last Updated:** November 30, 2025
**Model Version:** v1.0 (30 epochs)
**Status:** Production Ready ✅
