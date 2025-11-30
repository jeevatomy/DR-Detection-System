import os
from typing import List, Optional

import cv2
import numpy as np
import pandas as pd
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.utils import Sequence, to_categorical


def _circular_crop(img: np.ndarray) -> np.ndarray:
    """Apply circular crop to remove black borders around fundus image.

    Args:
        img: HxWxC uint8 image in RGB.

    Returns:
        cropped image with background outside circle kept as black.
    """
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    radius = min(center[0], center[1], w - center[0], h - center[1])
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)
    if img.ndim == 3:
        masked = cv2.bitwise_and(img, img, mask=mask)
    else:
        masked = cv2.bitwise_and(img, img, mask=mask)
    return masked


def _gaussian_blur(img: np.ndarray, sigma: float = 10.0) -> np.ndarray:
    """Apply Gaussian blur with given sigma using OpenCV.

    Uses ksize=(0,0) so OpenCV computes a kernel from sigma.
    """
    blurred = cv2.GaussianBlur(img, ksize=(0, 0), sigmaX=sigma, sigmaY=sigma)
    return blurred


def _load_and_preprocess(image_path: str, target_size=(224, 224)) -> np.ndarray:
    # Read with OpenCV (BGR), convert to RGB
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Circular crop
    img = _circular_crop(img)

    # Gaussian blur (sigma=10)
    img = _gaussian_blur(img, sigma=10.0)

    # Resize to target
    img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

    # Ensure 3 channels
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # Scale to [0,1]
    img = img.astype(np.float32) / 255.0
    return img


class TrainSequence(Sequence):
    """Keras Sequence to load and augment APTOS images with required preprocessing.

    This implements the paper's preprocessing pipeline and uses ImageDataGenerator
    for simple geometric augmentations (horizontal and vertical flips).
    """

    def __init__(self, csv_path: str = "data/train.csv", images_dir: str = "data/train_images",
                 batch_size: int = 16, target_size=(224, 224), shuffle: bool = True, num_classes: int = 5):
        self.df = pd.read_csv(csv_path)
        self.images_dir = images_dir
        self.batch_size = batch_size
        self.target_size = target_size
        self.shuffle = shuffle
        self.num_classes = num_classes

        # augmentation generator for random transforms
        self.aug = ImageDataGenerator(horizontal_flip=True, vertical_flip=True)

        self.indexes = np.arange(len(self.df))
        if self.shuffle:
            np.random.shuffle(self.indexes)

    def __len__(self):
        return int(np.ceil(len(self.df) / float(self.batch_size)))

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indexes)

    def _find_image_file(self, id_code: str) -> Optional[str]:
        # try common extensions
        for ext in (".png", ".jpg", ".jpeg"):
            p = os.path.join(self.images_dir, id_code + ext)
            if os.path.exists(p):
                return p
        # fallback: try raw id_code path
        p = os.path.join(self.images_dir, id_code)
        if os.path.exists(p):
            return p
        return None

    def __getitem__(self, idx):
        batch_indexes = self.indexes[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_df = self.df.iloc[batch_indexes]

        images = []
        labels = []
        for _, row in batch_df.iterrows():
            id_code = str(row["id_code"]).strip()
            lab = int(row["diagnosis"])
            img_path = self._find_image_file(id_code)
            if img_path is None:
                raise FileNotFoundError(f"Image for id {id_code} not found in {self.images_dir}")
            img = _load_and_preprocess(img_path, target_size=self.target_size)

            # apply random augmentation transforms
            img = self.aug.random_transform(img)

            images.append(img)
            labels.append(lab)

        x = np.stack(images, axis=0)
        y = to_categorical(labels, num_classes=self.num_classes)
        return x, y


def get_train_generator(batch_size: int = 16) -> TrainSequence:
    """Factory for the train generator with required augmentation and preprocessing."""
    return TrainSequence(csv_path=os.path.join("data", "train.csv"), images_dir=os.path.join("data", "train_images"),
                         batch_size=batch_size, target_size=(224, 224), shuffle=True, num_classes=5)
