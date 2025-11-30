# Quick Reference: Git LFS & Model Download

## For First-Time Users

### Step 1: Clone Repository
```bash
git clone https://github.com/jeevatomy/DR-Detection-System.git
cd DR_Detection_System
```

### Step 2: Download Models
```bash
python download_models.py
```

### Step 3: Start System
```bash
# Terminal 1: Backend
python -m uvicorn src.api:app --host localhost --port 8001

# Terminal 2: Frontend
cd frontend
npm start
```

### Step 4: Open Browser
```
http://localhost:3001
```

---

## Model Files

| File | Size | Use Case |
|------|------|----------|
| `fusion_dr_model.keras` | 277.8 MB | ✅ **USE THIS** |
| `fusion_dr_model.h5` | 276.8 MB | Fallback backup |
| `fusion_dr_model_final.keras` | 277.8 MB | Research only |

**All 3 are trained on 30 epochs with 77.35% accuracy.**

---

## Automatic Download Script

Run once to download all models:

```bash
python download_models.py
```

What it does:
- ✅ Checks Git LFS is installed
- ✅ Downloads models (877 MB total)
- ✅ Verifies file integrity
- ✅ Shows next steps

---

## Manual Download (If Script Fails)

### Method 1: Git LFS Pull
```bash
git lfs install
git lfs pull
```

### Method 2: Clone with LFS
```bash
git clone --depth 1 https://github.com/jeevatomy/DR-Detection-System.git
```

### Method 3: GitHub Releases
Visit: https://github.com/jeevatomy/DR-Detection-System/releases

---

## Documentation

- **MODELS.md** - Everything about models (2000+ lines)
- **GIT_LFS_SETUP.md** - LFS configuration details
- **README.md** - Quick start guide
- **SYSTEM_GUIDE.md** - Full system documentation

---

## LFS Status

Check current LFS files:
```bash
git lfs ls-files
```

Expected output:
```
01833d455d * fusion_dr_model.h5
f29c86bcdb * fusion_dr_model.keras
61390f4fa0 * fusion_dr_model_final.keras
```

---

## Troubleshooting

### Models are 13 KB text files?
```bash
git lfs install
git lfs pull
```

### Git LFS not installed?
**Windows:** https://github.com/git-lfs/git-lfs/releases  
**Mac:** `brew install git-lfs`  
**Linux:** `apt-get install git-lfs`

### Slow download?
- Download only primary model (277.8 MB)
- Use shallow clone: `git clone --depth 1 ...`
- Split downloads across sessions

### Can't find models after download?
```bash
# Verify files exist
ls -lh fusion_dr_model.*

# Should see files, not tiny text files
```

---

## API Endpoints

```
GET  http://localhost:8001/health          → Server status
GET  http://localhost:8001/model-info      → Model details
POST http://localhost:8001/predict         → Make prediction
```

---

## Storage Info

- **Total model size:** 850 MB (all 3 models)
- **Primary model:** 277.8 MB (recommended for production)
- **Backup model:** 276.8 MB (HDF5 format)
- **GitHub LFS limit:** 1 GB free per month (sufficient)

---

## For Repository Owner

### Monitor LFS Storage
```bash
# Check local LFS objects
git lfs fsck

# Check GitHub LFS usage
# Go to: https://github.com/jeevatomy/DR-Detection-System/settings
# Look for "Large File Storage" or "LFS"
```

### Add New Models
```bash
# Models with .h5, .keras automatically use LFS
git add new_model.keras
git commit -m "Add improved model v2"
git push origin main
```

---

## Performance Metrics

- **Model Accuracy:** 77.35%
- **Inference Time:** 5-8 seconds (CPU)
- **Input Size:** 224×224×3 RGB
- **Output Classes:** 5 (No DR, Mild, Moderate, Severe, Proliferative)
- **Epochs Trained:** 30
- **Training Time:** ~8 hours (on CPU)

---

## Key Links

- **Repository:** https://github.com/jeevatomy/DR-Detection-System
- **Latest Commits:** https://github.com/jeevatomy/DR-Detection-System/commits/main
- **Git LFS Docs:** https://git-lfs.github.com/

---

## Version Info

- **Model Version:** 1.0 (30 epochs)
- **Accuracy:** 77.35% validated
- **Framework:** TensorFlow 2.20.0 + Keras
- **Python Version:** 3.13+
- **Status:** Production Ready ✅

---

**Last Updated:** November 30, 2025
