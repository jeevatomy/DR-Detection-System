import tensorflow as tf
# Import local modules from src/ (when running from project root these are on sys.path)
from loss import focal_loss_fn
from model import ModelFusionLayer, build_fusion_model

# --- CONFIG ---
OLD_PATH = "fusion_dr_model.h5"
NEW_PATH = "fusion_dr_model.keras"

def main():
    print(f"Loading legacy model: {OLD_PATH}...")
    try:
        # Rebuild the architecture in code and load weights from the HDF5.
        # This avoids Lambda deserialization problems.
        print("Building model architecture...")
        model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
        print("Loading weights from HDF5...")
        model.load_weights(OLD_PATH)

        # Save in new native Keras format
        print(f"Saving to native format: {NEW_PATH}...")
        model.save(NEW_PATH, include_optimizer=False)
        print("✅ Success! You should now use 'fusion_dr_model.keras' for everything.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()