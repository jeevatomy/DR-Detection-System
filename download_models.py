#!/usr/bin/env python3
"""
Model Download Script for DR Detection System
============================================

This script downloads the pre-trained model files from GitHub LFS.
The models are stored using Git Large File Storage (LFS) for efficient storage and retrieval.

Usage:
    python download_models.py

Author: DR Detection System Team
Date: November 2025
"""

import os
import subprocess
import sys
from pathlib import Path

# Model information
MODELS = {
    'fusion_dr_model.keras': {
        'size': '277.8 MB',
        'epochs': 30,
        'accuracy': '77.35%',
        'description': 'Primary Keras model (native format, recommended)',
        'status': 'production-ready'
    },
    'fusion_dr_model.h5': {
        'size': '276.8 MB',
        'epochs': 30,
        'accuracy': '77.35%',
        'description': 'HDF5 format weights (backup/legacy)',
        'status': 'production-ready'
    },
    'fusion_dr_model_final.keras': {
        'size': '277.8 MB',
        'epochs': 30,
        'accuracy': '77.35%',
        'description': 'Final Keras model with Lambda layers (evaluation)',
        'status': 'evaluation-only'
    }
}


def print_header():
    """Print welcome header"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   DR Detection System - Model Download Utility              ║
    ║   Diabetic Retinopathy Detection using Deep CNN Fusion      ║
    ╚════════════════════════════════════════════════════════════╝
    """)


def print_model_info():
    """Display information about available models"""
    print("\n📦 Available Models:\n")
    print("-" * 80)
    
    for model_name, info in MODELS.items():
        status_symbol = "✅" if info['status'] == 'production-ready' else "📊"
        print(f"\n{status_symbol} {model_name}")
        print(f"   Size:        {info['size']}")
        print(f"   Epochs:      {info['epochs']}")
        print(f"   Accuracy:    {info['accuracy']}")
        print(f"   Description: {info['description']}")
        print(f"   Status:      {info['status']}")
    
    print("\n" + "-" * 80)


def check_git_lfs():
    """Check if Git LFS is installed"""
    try:
        result = subprocess.run(['git', 'lfs', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"\n✅ Git LFS installed: {result.stdout.strip()}")
            return True
        else:
            print("\n❌ Git LFS not installed or not working")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("\n❌ Git LFS not found. Please install it:")
        print("   Windows: https://github.com/git-lfs/git-lfs/releases")
        print("   Mac:     brew install git-lfs")
        print("   Linux:   apt-get install git-lfs")
        return False


def download_models():
    """Download models using git lfs pull"""
    print("\n📥 Downloading models from GitHub LFS...\n")
    
    try:
        # First, fetch LFS metadata
        print("Step 1: Fetching LFS metadata...")
        subprocess.run(['git', 'lfs', 'fetch'], check=True, cwd=Path(__file__).parent)
        print("✅ LFS metadata fetched")
        
        # Then checkout (pull) the files
        print("\nStep 2: Pulling model files...")
        subprocess.run(['git', 'lfs', 'checkout'], check=True, cwd=Path(__file__).parent)
        print("✅ Model files downloaded")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error downloading models: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def verify_models():
    """Verify that model files exist and have correct size indicators"""
    print("\n🔍 Verifying downloaded models...\n")
    
    project_root = Path(__file__).parent
    models_exist = True
    
    for model_name in MODELS.keys():
        model_path = project_root / model_name
        
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✅ {model_name}: {size_mb:.1f} MB")
        else:
            print(f"❌ {model_name}: NOT FOUND")
            models_exist = False
    
    return models_exist


def manual_download_instructions():
    """Print manual download instructions"""
    print("""
    📖 Manual Download Instructions:
    ================================
    
    If automatic download fails, you can manually download the models:
    
    1. Clone the repository with LFS:
       git clone --depth 1 https://github.com/jeevatomy/DR-Detection-System.git
    
    2. Or if already cloned, pull LFS files:
       git lfs pull
    
    3. Alternative: Download from GitHub Releases:
       https://github.com/jeevatomy/DR-Detection-System/releases
    
    4. Place model files in the project root directory:
       - fusion_dr_model.keras
       - fusion_dr_model.h5 (optional backup)
       - fusion_dr_model_final.keras (optional evaluation)
    """)


def main():
    """Main execution"""
    print_header()
    print_model_info()
    
    # Check Git LFS
    if not check_git_lfs():
        print("\n⚠️  Git LFS is required for downloading model files.")
        manual_download_instructions()
        sys.exit(1)
    
    # Download models
    if not download_models():
        print("\n⚠️  Automatic download failed.")
        manual_download_instructions()
        sys.exit(1)
    
    # Verify models
    if verify_models():
        print("\n" + "=" * 80)
        print("✅ SUCCESS! All models downloaded successfully!")
        print("=" * 80)
        print("\n🚀 You can now run:")
        print("   1. Backend:  python -m uvicorn src.api:app --host localhost --port 8001")
        print("   2. Frontend: npm start (in frontend/ directory)")
        print("\n📊 Then open http://localhost:3001 in your browser")
        return 0
    else:
        print("\n⚠️  Some models are missing.")
        manual_download_instructions()
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
