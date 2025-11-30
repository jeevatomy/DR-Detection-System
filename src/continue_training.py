import os
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger
from preprocessing import get_train_generator
from loss import focal_loss_fn
from model import ModelFusionLayer, build_fusion_model  # use builder to avoid HDF5 lambda issues

# --- CONFIGURATION ---
# We load the model you just built (10 epochs)
OLD_MODEL_PATH = "fusion_dr_model.h5" 

# We save the final model here (40 epochs total)
NEW_MODEL_PATH = "fusion_dr_model_final.keras" 

# Config from paper + safety
BATCH_SIZE = 8       # Keep this safe to avoid OOM
EXTRA_EPOCHS = 30    # 10 existing + 30 new = 40 Total (Matches Paper)

def main():
    # 1. GPU Safety Block (Crucial for Windows)
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            print(f"GPU Error: {e}")

    # 2. Load Data
    print(f"Loading Data Generator (Batch Size: {BATCH_SIZE})...")
    train_gen = get_train_generator(batch_size=BATCH_SIZE)

    # 3. Load the Existing 10-Epoch Model
    print(f"Loading previous brain: {OLD_MODEL_PATH}...")
    
    if not os.path.exists(OLD_MODEL_PATH):
        print(f"❌ Error: {OLD_MODEL_PATH} not found. Did you finish the first 10 epochs?")
        return

    try:
        # Rebuild architecture and load weights from HDF5 to avoid Lambda deserialization issues
        print("Rebuilding model architecture...")
        model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
        print(f"Loading weights from {OLD_MODEL_PATH}...")
        model.load_weights(OLD_MODEL_PATH)
        print("✅ Weights loaded successfully. Ready for Phase 2.")
    except Exception as e:
        print(f"❌ Error loading weights: {e}")
        return

    # Compile model for further training (use a lower LR for fine-tuning)
    opt = tf.keras.optimizers.Adam(learning_rate=1e-5)
    model.compile(optimizer=opt, loss=focal_loss_fn, metrics=[tf.keras.metrics.CategoricalAccuracy()])

    # 4. Define Smart Callbacks (The "Secret Sauce" from the Paper)
    
    # A. Checkpoint: Saves the model every time accuracy improves.
    # If the PC crashes, you don't lose progress.
    checkpoint = ModelCheckpoint(
        NEW_MODEL_PATH,
        monitor='categorical_accuracy',
        verbose=1,
        save_best_only=True,
        mode='max'
    )

    # B. Learning Rate Decay: The paper uses this to fine-tune results.
    # If loss doesn't improve for 3 epochs, it cuts learning rate by half.
    reduce_lr = ReduceLROnPlateau(
        monitor='loss', 
        factor=0.5, 
        patience=3, 
        min_lr=1e-6,
        verbose=1
    )
    
    # C. Logger: Saves a text file of your progress
    csv_logger = CSVLogger('training_log_phase2.csv', append=True)

    # 5. Start Training
    print(f"Starting Phase 2 Training for {EXTRA_EPOCHS} more epochs...")
    print("This will take significantly longer, but will yield higher accuracy.")
    
    try:
        # Run training (omit workers/use_multiprocessing to avoid platform mismatches)
        model.fit(
            train_gen,
            epochs=EXTRA_EPOCHS,
            callbacks=[checkpoint, reduce_lr, csv_logger]
        )
        print(f"✅ Training Finished. Final model saved as {NEW_MODEL_PATH}")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted! Saving whatever we have so far...")
        model.save("fusion_dr_model_interrupted.keras")

if __name__ == "__main__":
    main()