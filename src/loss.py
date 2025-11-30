import tensorflow as tf


def focal_loss(gamma: float = 2.0, alpha: float = 0.25):
    """Create a focal loss function for multi-class classification.

    Returns a function usable as a Keras loss.
    """

    def loss(y_true, y_pred):
        # y_true: one-hot, y_pred: probabilities (after softmax)
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)
        cross_entropy = -y_true * tf.math.log(y_pred)
        weights = alpha * tf.pow(1 - y_pred, gamma)
        loss_val = weights * cross_entropy
        return tf.reduce_sum(loss_val, axis=1)

    return loss


# For convenience export a pre-configured focal loss
focal_loss_fn = focal_loss(gamma=2.0, alpha=0.25)
