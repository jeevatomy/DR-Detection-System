import os
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf

# Allow loading legacy HDF5 models that contain Python lambda in Lambda layers.
# This is potentially unsafe if the file is untrusted; here we enable it because
# the model was created in this workspace.
try:
    from keras import config as keras_config
    keras_config.enable_unsafe_deserialization()
except Exception:
    # older/newer TF/Keras versions may differ; ignore if not available
    pass

from model import ModelFusionLayer, build_fusion_model

# reuse preprocessing helper from our module
from preprocessing import _load_and_preprocess


def find_image(images_dir, id_code):
    for ext in (".png", ".jpg", ".jpeg"):
        p = os.path.join(images_dir, id_code + ext)
        if os.path.exists(p):
            return p
    p = os.path.join(images_dir, id_code)
    if os.path.exists(p):
        return p
    return None


def main(args):
    model_path = args.model or os.path.join(os.getcwd(), "fusion_dr_model.h5")
    print("Loading model (compile=False, safe_mode=False)...", model_path)
    # Pass safe_mode=False to allow deserializing Lambda layers that use Python
    # lambdas. This is safe here because the model file was created inside this
    # project. Do NOT do this with untrusted files.
    # Rebuild the model architecture from code and load weights from the HDF5.
    # This avoids deserialization issues with Lambda layers/custom objects.
    print("Building model architecture and loading weights from:", model_path)
    model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
    model.load_weights(model_path)
    print("Model built and weights loaded.")

    csv_path = args.csv or os.path.join(os.getcwd(), "data", "train.csv")
    images_dir = args.images or os.path.join(os.getcwd(), "data", "train_images")

    df = pd.read_csv(csv_path)
    ids = df["id_code"].astype(str).tolist()

    sample_ids = ids[: args.num] if args.num > 0 else ids[:5]

    imgs = []
    found = []
    for id_code in sample_ids:
        p = find_image(images_dir, id_code)
        if p is None:
            print(f"Warning: image for id {id_code} not found in {images_dir}")
            continue
        img = _load_and_preprocess(p, target_size=(224, 224))
        imgs.append(img)
        found.append(id_code)

    if len(imgs) == 0:
        print("No images found to run inference on. Exiting.")
        return

    x = np.stack(imgs, axis=0)
    print(f"Running inference on {x.shape[0]} samples...")
    preds = model.predict(x)

    # Map class indices to human-readable severity levels
    severity_map = {
        0: "No DR",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
        4: "Proliferative",
    }

    for id_code, p in zip(found, preds):
        top_idx = int(np.argmax(p))
        top_prob = float(np.max(p))
        label = severity_map.get(top_idx, "Unknown")
        # Print both numeric class and human-readable severity level
        print(f"{id_code}: predicted class={top_idx} ({label}) prob={top_prob:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test fusion_dr_model inference on a few APTOS images")
    parser.add_argument("--model", help="Path to model .h5 file", default=None)
    parser.add_argument("--csv", help="Path to train.csv", default=None)
    parser.add_argument("--images", help="Path to train_images dir", default=None)
    parser.add_argument("--num", help="Number of samples to run", type=int, default=5)
    args = parser.parse_args()
    main(args)
