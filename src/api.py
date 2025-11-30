"""
FastAPI Backend for Diabetic Retinopathy Detection System
Serves predictions from the trained fusion model via REST API
"""

import os
import io
import cv2
import numpy as np
import tensorflow as tf
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import logging
import sys

# Add src directory to path for relative imports
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import custom model components
from preprocessing import _circular_crop, _gaussian_blur
from loss import focal_loss_fn
from model import ModelFusionLayer, build_fusion_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model variable
model = None

# Class mapping for output
CLASS_NAMES = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative"
}

def load_keras_model():
    """
    Load the trained Keras model with custom objects.
    Attempts to load fusion_dr_model.keras (30-epoch clean version) first, 
    falls back to rebuilding from HDF5 if needed.
    """
    global model
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path_keras = os.path.join(root_dir, "fusion_dr_model.keras")  # 30-epoch clean version
    model_path_h5 = os.path.join(root_dir, "fusion_dr_model.h5")  # 30-epoch weights
    
    custom_objects = {
        "focal_loss_fixed": focal_loss_fn,
        "ModelFusionLayer": ModelFusionLayer
    }
    
    try:
        # Try loading native Keras format first
        if os.path.exists(model_path_keras):
            logger.info(f"Loading model from {model_path_keras}")
            model = tf.keras.models.load_model(
                model_path_keras,
                custom_objects=custom_objects,
                compile=False
            )
            logger.info("✅ Model loaded successfully from .keras file")
            return model
    except Exception as e:
        logger.warning(f"Failed to load .keras model: {e}")
    
    try:
        # Fallback: rebuild architecture and load weights from HDF5
        if os.path.exists(model_path_h5):
            logger.info(f"Rebuilding model architecture and loading weights from {model_path_h5}")
            model = build_fusion_model(input_shape=(224, 224, 3), num_classes=5)
            model.load_weights(model_path_h5)
            logger.info("✅ Model rebuilt and weights loaded from HDF5")
            return model
    except Exception as e:
        logger.error(f"Failed to rebuild and load weights: {e}")
        raise RuntimeError(f"Could not load model from either {model_path_keras} or {model_path_h5}")
    
    raise FileNotFoundError(f"Model files not found at {model_path_keras} or {model_path_h5}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to load model on startup and cleanup on shutdown
    """
    # Startup: Load model
    logger.info("🚀 Starting up... Loading model")
    load_keras_model()
    logger.info("✅ Model loaded successfully")
    yield
    # Shutdown: Cleanup (if needed)
    logger.info("🛑 Shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Diabetic Retinopathy Detection API",
    description="AI-powered DR detection system using deep learning fusion model",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def preprocess_image(image_bytes: bytes, target_size: tuple = (224, 224)) -> np.ndarray:
    """
    Preprocess image exactly as done during training:
    1. Load image and convert to RGB
    2. Apply circular crop
    3. Apply Gaussian blur (sigma=10)
    4. Resize to target_size
    5. Normalize (divide by 255.0)
    
    Args:
        image_bytes: Raw image bytes
        target_size: Target image size (default: 224x224)
    
    Returns:
        Preprocessed image as numpy array
    """
    try:
        # Load image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL to OpenCV format (BGR)
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply circular crop (mask out background)
        image_cv = _circular_crop(image_cv)
        
        # Apply Gaussian blur (sigma=10)
        image_cv = _gaussian_blur(image_cv, sigma=10)
        
        # Resize to 224x224
        image_cv = cv2.resize(image_cv, target_size)
        
        # Convert BGR back to RGB for model input
        image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
        
        # Normalize: divide by 255.0
        image_rgb = image_rgb.astype(np.float32) / 255.0
        
        logger.info(f"Image preprocessed successfully. Shape: {image_rgb.shape}")
        return image_rgb
    
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise ValueError(f"Failed to preprocess image: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "service": "Diabetic Retinopathy Detection API"
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Prediction endpoint.
    
    Accepts: Image file (PNG, JPG, JPEG)
    Returns: Diagnosis, confidence, and probability distribution
    
    Args:
        file: Uploaded image file
    
    Returns:
        JSON with diagnosis, confidence, and per-class probabilities
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Validate file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file bytes
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Preprocess image
        logger.info(f"Processing image: {file.filename}")
        preprocessed_image = preprocess_image(contents)
        
        # Add batch dimension: (1, 224, 224, 3)
        input_batch = np.expand_dims(preprocessed_image, axis=0)
        
        # Run inference
        logger.info("Running model inference")
        predictions = model.predict(input_batch, verbose=0)
        probabilities = predictions[0]  # Shape: (5,)
        
        # Get predicted class
        predicted_class = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_class])
        
        # Map class index to name
        diagnosis = CLASS_NAMES[predicted_class]
        
        # Build probability distribution
        prob_dict = {CLASS_NAMES[i]: float(probabilities[i]) for i in range(5)}
        
        # Determine severity level for response
        severity = "Low Risk" if predicted_class == 0 else "Medium Risk" if predicted_class == 1 else "High Risk"
        
        logger.info(f"Prediction complete: {diagnosis} (confidence: {confidence:.4f})")
        
        return JSONResponse({
            "status": "success",
            "diagnosis": diagnosis,
            "severity": severity,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "recommended_action": get_recommended_action(predicted_class)
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


def get_recommended_action(class_index: int) -> str:
    """
    Get recommended clinical action based on diagnosis.
    
    Args:
        class_index: Predicted class index (0-4)
    
    Returns:
        Recommended action string
    """
    recommendations = {
        0: "No diabetic retinopathy detected. Continue regular checkups annually.",
        1: "Mild DR detected. Schedule comprehensive eye exam within 3 months.",
        2: "Moderate DR detected. Urgent referral to ophthalmologist recommended.",
        3: "Severe DR detected. Immediate ophthalmologist consultation required.",
        4: "Proliferative DR detected. URGENT - Refer to retinal specialist immediately."
    }
    return recommendations.get(class_index, "Unknown diagnosis")


@app.get("/model-info")
async def model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_name": "Fusion DR Detection Model",
        "architecture": "VGG16 + ResNet50 + DenseNet121 with Attention",
        "input_shape": (224, 224, 3),
        "num_classes": 5,
        "classes": CLASS_NAMES,
        "total_parameters": model.count_params(),
        "trainable_parameters": sum([tf.size(w).numpy() for w in model.trainable_weights])
    }


if __name__ == "__main__":
    import uvicorn
    # Run with: uvicorn api:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
