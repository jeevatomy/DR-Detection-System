import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns

from preprocessing import _load_and_preprocess
from loss import focal_loss_fn
from model import ModelFusionLayer, build_fusion_model

# --- CONFIG ---
MODEL_FILE = "fusion_dr_model_final.keras" 

def enable_gpu_memory_growth():
    try:
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
    except Exception as e:
        print("Warning:", e)

class EvalSequence(tf.keras.utils.Sequence):
    def __init__(self, df, images_dir, batch_size=8, target_size=(224, 224), num_classes=5):
        self.df = df.reset_index(drop=True)
        self.images_dir = images_dir
        self.batch_size = batch_size
        self.target_size = target_size
        self.num_classes = num_classes

    def __len__(self):
        return int(np.ceil(len(self.df) / float(self.batch_size)))

    def _find_image_file(self, id_code: str):
        for ext in (".png", ".jpg", ".jpeg"):
            p = os.path.join(self.images_dir, id_code + ext)
            if os.path.exists(p): return p
        p = os.path.join(self.images_dir, id_code)
        if os.path.exists(p): return p
        return None

    def __getitem__(self, idx):
        batch_df = self.df.iloc[idx * self.batch_size:(idx + 1) * self.batch_size]
        images = []
        labels = []
        ids = []
        for _, row in batch_df.iterrows():
            id_code = str(row['id_code']).strip()
            lab = int(row['diagnosis'])
            img_path = self._find_image_file(id_code)
            if img_path:
                img = _load_and_preprocess(img_path, target_size=self.target_size)
                images.append(img)
                labels.append(lab)
                ids.append(id_code)
        
        if not images: return np.array([]), np.array([]), []
        return np.stack(images, axis=0), np.array(labels, dtype=np.int32), ids

def main():
    enable_gpu_memory_growth()
    root = os.getcwd()
    os.makedirs(os.path.join(root, 'evaluation'), exist_ok=True)
    csv_path = os.path.join(root, 'data', 'train.csv')
    images_dir = os.path.join(root, 'data', 'train_images')
    model_path = os.path.join(root, MODEL_FILE)

    if not os.path.exists(model_path):
        print(f"❌ Error: Could not find {MODEL_FILE}.")
        return

    print(f"🔄 Loading FINAL High-Accuracy Model: {MODEL_FILE}...")

    # Load model: try direct load first, then fallback to rebuilding + loading weights
    model = None
    custom_objects = {"focal_loss_fixed": focal_loss_fn, "ModelFusionLayer": ModelFusionLayer}
    if os.path.exists(model_path):
        try:
            model = tf.keras.models.load_model(model_path, custom_objects=custom_objects, compile=False)
            print("✅ Model loaded from native file!")
        except Exception as e:
            print(f"⚠️ Direct .keras load failed: {e}")
            # Try rebuilding architecture and loading weights from legacy HDF5
            h5_path = os.path.join(root, 'fusion_dr_model.h5')
            if os.path.exists(h5_path):
                print("Rebuilding architecture and loading weights from HDF5:", h5_path)
                try:
                    model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
                    model.load_weights(h5_path)
                    print("✅ Model rebuilt and weights loaded from HDF5")
                except Exception as e2:
                    print(f"❌ Failed to rebuild/load weights: {e2}")
                    return
            else:
                # As a last resort enable unsafe deserialization and try load_model again
                try:
                    from keras import config as keras_config
                    keras_config.enable_unsafe_deserialization()
                    model = tf.keras.models.load_model(model_path, custom_objects=custom_objects, compile=False)
                    print("✅ Model loaded after enabling unsafe deserialization")
                except Exception as e3:
                    print(f"❌ Final load attempt failed: {e3}")
                    return
    else:
        print(f"❌ Error: Could not find {MODEL_FILE}. Did continue_training.py finish?")
        return

    # Prepare Data
    df = pd.read_csv(csv_path)
    # Stratified Split
    try:
        from sklearn.model_selection import train_test_split
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['diagnosis'])
    except:
        val_df = df.iloc[int(len(df)*0.8):]

    print(f"📊 Evaluating on {len(val_df)} validation images...")
    
    # Run Prediction
    eval_seq = EvalSequence(val_df, images_dir, batch_size=8)
    y_true, y_pred, y_probs = [], [], []

    print("Running predictions (this takes ~3 mins)...")
    for i in range(len(eval_seq)):
        x, y, _ = eval_seq[i]
        if len(x) == 0: continue
        probs = model.predict(x, verbose=0)
        y_true.extend(y)
        y_pred.extend(np.argmax(probs, axis=1))
        y_probs.extend(probs)
        if i % 10 == 0: print(f"Batch {i}/{len(eval_seq)} done...")
    
    # Calculate Metrics
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, cohen_kappa_score
    
    acc = accuracy_score(y_true, y_pred)
    kappa = cohen_kappa_score(y_true, y_pred, weights='quadratic')
    
    print("\n" + "="*30)
    print(f"🏆 FINAL RESULTS (Epoch 40 Model)")
    print("="*30)
    print(f"Accuracy:    {acc:.4f} (Paper: ~0.95)")
    print(f"Kappa Score: {kappa:.4f} (Paper: ~0.96)")
    print("-" * 30)
    
    # Classification Report
    report = classification_report(y_true, y_pred, target_names=["No DR", "Mild", "Moderate", "Severe", "Proliferative"])
    print(report)
    
    # Save Report to File
    with open("evaluation/final_report.txt", "w") as f:
        f.write(f"Accuracy: {acc}\nKappa: {kappa}\n\n{report}")

    # Save Matrix Graph
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', xticklabels=["No", "Mild", "Mod", "Sev", "Pro"], yticklabels=["No", "Mild", "Mod", "Sev", "Pro"])
    plt.title(f'Confusion Matrix (Acc: {acc:.2%})')
    plt.savefig('evaluation/final_confusion_matrix.png')
    print("✅ Saved matrix to evaluation/final_confusion_matrix.png")

if __name__ == '__main__':
    main()