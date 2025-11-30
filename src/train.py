import os

import tensorflow as tf

from preprocessing import get_train_generator
from model import build_fusion_model
from loss import focal_loss


def main():
    # reduce batch size to lower OOM risk for the large fusion model
    batch_size = 8
    epochs = 10

    # GPU safety: set memory growth so TensorFlow does not grab all GPU memory at once
    try:
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            logical_gpus = tf.config.experimental.list_logical_devices('GPU')
            print(f"Detected {len(gpus)} Physical GPUs, {len(logical_gpus)} Logical GPUs. Enabled memory growth.")
        else:
            print("No GPU detected, running on CPU.")
    except Exception as e:
        # Memory growth may not be supported in some TF builds; warn but continue
        print("Warning: Could not set TensorFlow GPU memory growth:", e)

    print("Preparing data generator...")
    train_gen = get_train_generator(batch_size=batch_size)

    print("Building model...")
    model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)

    print("Compiling model with Adam and Focal Loss...")
    opt = tf.keras.optimizers.Adam(learning_rate=1e-4)
    loss_fn = focal_loss(gamma=2.0, alpha=0.25)
    model.compile(optimizer=opt, loss=loss_fn, metrics=[tf.keras.metrics.CategoricalAccuracy()])

    print(model.summary())

    # Fit
    print("Starting training for {} epochs".format(epochs))
    # Prepare callbacks: save native Keras format (.keras) during training to avoid
    # HDF5 lambda/custom-object issues when reloading the full model later.
    ckpt_path = os.path.join(os.getcwd(), "fusion_dr_model.keras")
    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        ckpt_path,
        save_best_only=True,
        monitor="loss",
        mode="min",
        save_weights_only=False,
        save_format="keras",
    )

    model.fit(train_gen, epochs=epochs, callbacks=[checkpoint_cb])

    # Save model
    # Save final model in both native Keras and legacy HDF5 formats for compatibility.
    keras_out = os.path.join(os.getcwd(), "fusion_dr_model.keras")
    h5_out = os.path.join(os.getcwd(), "fusion_dr_model.h5")
    print(f"Saving final model to {keras_out} (native Keras format)")
    model.save(keras_out, include_optimizer=False)
    print(f"Also saving legacy HDF5 to {h5_out}")
    # Save HDF5 for backward compatibility; include_optimizer=False to avoid
    # serializing optimizer state which can require custom objects.
    model.save(h5_out, include_optimizer=False)


if __name__ == "__main__":
    main()
