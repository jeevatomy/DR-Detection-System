import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf

from preprocessing import _load_and_preprocess
from model import build_fusion_model
from loss import focal_loss


def enable_gpu_memory_growth():
    try:
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"Enabled memory growth for {len(gpus)} GPU(s)")
        else:
            print("No GPU detected, running on CPU.")
    except Exception as e:
        print("Warning: could not set memory growth:", e)


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
            if os.path.exists(p):
                return p
        p = os.path.join(self.images_dir, id_code)
        if os.path.exists(p):
            return p
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
            if img_path is None:
                raise FileNotFoundError(f"Image for id {id_code} not found in {self.images_dir}")
            img = _load_and_preprocess(img_path, target_size=self.target_size)
            images.append(img)
            labels.append(lab)
            ids.append(id_code)
        x = np.stack(images, axis=0)
        y = np.array(labels, dtype=np.int32)
        return x, y, ids


def main():
    enable_gpu_memory_growth()

    # Paths
    root = os.getcwd()
    csv_path = os.path.join(root, 'data', 'train.csv')
    images_dir = os.path.join(root, 'data', 'train_images')
    keras_path = os.path.join(root, 'fusion_dr_model.keras')
    h5_path = os.path.join(root, 'fusion_dr_model.h5')

    df = pd.read_csv(csv_path)

    # Create a stratified split for validation
    try:
        from sklearn.model_selection import train_test_split
        strat = df['diagnosis']
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=strat)
    except Exception:
        # fallback: simple split
        n = len(df)
        split = int(n * 0.8)
        train_df = df.iloc[:split]
        val_df = df.iloc[split:]

    print(f"Validation set size: {len(val_df)} samples")

    # Load model: prefer native .keras if present; else rebuild+load_weights from h5
    model = None
    if os.path.exists(keras_path):
        try:
            print("Loading model from native Keras file:", keras_path)
            model = tf.keras.models.load_model(keras_path, compile=False)
        except Exception as e:
            print("Could not load .keras directly, will rebuild and load weights. Error:", e)

    if model is None:
        if os.path.exists(h5_path):
            print("Rebuilding model architecture and loading weights from HDF5")
            model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
            model.load_weights(h5_path)
        else:
            raise FileNotFoundError('No model file found (.keras or .h5)')

    # Compile for evaluation (loss must be available)
    opt = tf.keras.optimizers.Adam(learning_rate=1e-4)
    loss_fn = focal_loss(gamma=2.0, alpha=0.25)
    model.compile(optimizer=opt, loss=loss_fn, metrics=[tf.keras.metrics.CategoricalAccuracy()])

    # Eval generator (no augmentation)
    batch_size = 8
    eval_seq = EvalSequence(val_df, images_dir, batch_size=batch_size)

    # Collect predictions
    all_ids = []
    all_true = []
    all_probs = []

    for i in range(len(eval_seq)):
        x_batch, y_batch, ids = eval_seq[i]
        probs = model.predict(x_batch)
        all_ids.extend(ids)
        all_true.extend(y_batch.tolist())
        all_probs.extend(probs.tolist())

    y_true = np.array(all_true, dtype=int)
    y_probs = np.array(all_probs, dtype=float)
    y_pred = np.argmax(y_probs, axis=1)

    # Compute metrics
    results = {}
    try:
        from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
        results['accuracy'] = float(accuracy_score(y_true, y_pred))
        results['classification_report'] = classification_report(y_true, y_pred, output_dict=True)
        cm = confusion_matrix(y_true, y_pred)
        results['confusion_matrix_shape'] = cm.shape
    except Exception as e:
        print('sklearn not available or error computing metrics:', e)
        # fallback simple accuracy and per-class counts
        acc = float(np.mean(y_true == y_pred))
        results['accuracy'] = acc
        results['note'] = 'classification_report not available; sklearn missing'
        cm = None

    # Save metrics and predictions
    out_dir = os.path.join(root, 'evaluation')
    os.makedirs(out_dir, exist_ok=True)

    metrics_path = os.path.join(out_dir, 'evaluation_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)

    preds_df = pd.DataFrame({
        'id_code': all_ids,
        'true_label': y_true.tolist(),
        'pred_label': y_pred.tolist(),
    })
    # add probability columns
    for c in range(y_probs.shape[1]):
        preds_df[f'prob_{c}'] = y_probs[:, c]

    preds_df['pred_prob'] = np.max(y_probs, axis=1)

    preds_csv = os.path.join(out_dir, 'predictions.csv')
    preds_df.to_csv(preds_csv, index=False)

    if cm is not None:
        cm_df = pd.DataFrame(cm)
        cm_df.to_csv(os.path.join(out_dir, 'confusion_matrix.csv'), index=False)

    print('Evaluation complete. Metrics saved to', metrics_path)
    print('Predictions saved to', preds_csv)


if __name__ == '__main__':
    main()
