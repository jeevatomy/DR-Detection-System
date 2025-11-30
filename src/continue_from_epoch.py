import os
import tensorflow as tf

from preprocessing import get_train_generator
from loss import focal_loss


def main():
    # resume settings
    batch_size = 8
    start_epoch = 10  # epochs already completed
    target_epochs = 30

    # GPU safety
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

    # Load model (native Keras format) if available, else rebuild and load weights
    keras_path = os.path.join(os.getcwd(), "fusion_dr_model.keras")
    h5_path = os.path.join(os.getcwd(), "fusion_dr_model.h5")

    # Prefer loading weights from the legacy HDF5 if present (robust), else try
    # loading the native .keras full model (may contain Lambda layers).
    if os.path.exists(h5_path):
        print("Rebuilding architecture and loading weights from HDF5:", h5_path)
        from model import build_fusion_model
        model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
        model.load_weights(h5_path)
    elif os.path.exists(keras_path):
        print("Attempting to load full model from native Keras file:", keras_path)
        # If the .keras contains Python lambdas we may need to allow unsafe deserialization
        try:
            from keras import config as keras_config
            keras_config.enable_unsafe_deserialization()
        except Exception:
            pass
        # Provide custom_objects if necessary
        from model import ModelFusionLayer
        model = tf.keras.models.load_model(keras_path, compile=False, custom_objects={"ModelFusionLayer": ModelFusionLayer})
    else:
        raise FileNotFoundError("No saved model found to resume from (.h5 or .keras)")

    # Recompile with same optimizer/loss
    opt = tf.keras.optimizers.Adam(learning_rate=1e-4)
    loss_fn = focal_loss(gamma=2.0, alpha=0.25)
    model.compile(optimizer=opt, loss=loss_fn, metrics=[tf.keras.metrics.CategoricalAccuracy()])

    # Data generator
    train_gen = get_train_generator(batch_size=batch_size)

    # Optional: checkpoint callback to save best model in native format
    ckpt_path = os.path.join(os.getcwd(), "fusion_dr_model.keras")
    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        ckpt_path, save_best_only=False, monitor="loss", save_weights_only=False
    )

    print(f"Resuming training from epoch {start_epoch} to {target_epochs} (batch_size={batch_size})")
    model.fit(train_gen, epochs=target_epochs, initial_epoch=start_epoch, callbacks=[checkpoint_cb])

    # Save final model
    print("Saving final model to native Keras format...")
    model.save(ckpt_path, include_optimizer=False)
    print("Resume training complete.")


if __name__ == "__main__":
    main()
