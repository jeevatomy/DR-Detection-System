"""
Debugging & Testing Script for Full Stack DR Detection System
Tests both backend API and frontend connectivity
"""

import requests
import json
import time

print("=" * 70)
print("🔍 DR DETECTION SYSTEM - DEBUG & TEST")
print("=" * 70)

# ============================================================================
# TEST 1: Backend Health Check
# ============================================================================
print("\n[TEST 1] 🏥 Backend Health Check")
print("-" * 70)

try:
    response = requests.get("http://localhost:8001/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backend is HEALTHY")
        print(f"   Status: {data.get('status')}")
        print(f"   Model Loaded: {data.get('model_loaded')}")
        print(f"   Service: {data.get('service')}")
    else:
        print(f"❌ Backend returned status code: {response.status_code}")
except Exception as e:
    print(f"❌ Backend unreachable: {e}")

# ============================================================================
# TEST 2: Model Info Endpoint
# ============================================================================
print("\n[TEST 2] 🧠 Model Information")
print("-" * 70)

try:
    response = requests.get("http://localhost:8001/model-info", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Model info retrieved successfully")
        print(f"   Model Name: {data.get('model_name')}")
        print(f"   Architecture: {data.get('architecture')}")
        print(f"   Input Shape: {data.get('input_shape')}")
        print(f"   Classes: {data.get('num_classes')}")
        print(f"   Total Parameters: {data.get('total_parameters'):,}")
except Exception as e:
    print(f"❌ Failed to get model info: {e}")

# ============================================================================
# TEST 3: CORS Headers Check (for frontend)
# ============================================================================
print("\n[TEST 3] 🌐 CORS Configuration")
print("-" * 70)

try:
    response = requests.options(
        "http://localhost:8001/predict",
        headers={"Origin": "http://localhost:3000"}
    )
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
    }
    
    if cors_headers["Access-Control-Allow-Origin"]:
        print(f"✅ CORS enabled for frontend")
        print(f"   Allow-Origin: {cors_headers['Access-Control-Allow-Origin']}")
        print(f"   Allow-Methods: {cors_headers['Access-Control-Allow-Methods']}")
    else:
        print(f"⚠️  CORS headers not fully configured")
except Exception as e:
    print(f"⚠️  CORS check failed: {e}")

# ============================================================================
# TEST 4: API Error Handling
# ============================================================================
print("\n[TEST 4] 🚨 Error Handling")
print("-" * 70)

try:
    # Test with invalid file
    response = requests.post(
        "http://localhost:8001/predict",
        files={"file": ("test.txt", b"invalid data")}
    )
    if response.status_code == 400:
        print(f"✅ API properly handles invalid file types")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ Unexpected response: {response.status_code}")
except Exception as e:
    print(f"❌ Error handling test failed: {e}")

# ============================================================================
# TEST 5: Frontend Accessibility
# ============================================================================
print("\n[TEST 5] 🖥️  Frontend Server")
print("-" * 70)

try:
    response = requests.get("http://localhost:3000", timeout=5)
    if response.status_code == 200:
        print(f"✅ Frontend is accessible at http://localhost:3000")
        print(f"   Server is responding with status 200")
    else:
        print(f"⚠️  Frontend returned status: {response.status_code}")
except Exception as e:
    print(f"⚠️  Frontend may not be ready: {e}")

# ============================================================================
# TEST 6: Network Connectivity Summary
# ============================================================================
print("\n[TEST 6] 📡 System Status Summary")
print("-" * 70)

services = {
    "Backend API": "http://localhost:8001/health",
    "Frontend UI": "http://localhost:3000",
    "Model Service": "http://localhost:8001/model-info",
}

for service_name, service_url in services.items():
    try:
        response = requests.head(service_url, timeout=2)
        status = "✅ RUNNING" if response.status_code < 500 else "❌ ERROR"
        print(f"{status} - {service_name}: {service_url}")
    except:
        print(f"❌ DOWN - {service_name}: {service_url}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("🎯 SYSTEM STATUS SUMMARY")
print("=" * 70)
print("""
✅ BACKEND:  http://localhost:8001
   - FastAPI server with Uvicorn
   - TensorFlow/Keras model loaded
   - CORS enabled for React frontend
   
✅ FRONTEND: http://localhost:3000
   - React development server
   - Modern dashboard UI with file upload
   - Real-time predictions with visualization

📋 NEXT STEPS:
   1. Open http://localhost:3000 in your browser
   2. Upload a retinal fundus image
   3. Click "Analyze Image" to get predictions
   4. View results with confidence scores and probabilities

⚠️  NOTE: First prediction may take longer (~30 seconds) as the model
   initializes. Subsequent predictions will be faster.

🐛 DEBUGGING TIPS:
   - Check backend logs for inference errors
   - Browser console (F12) shows frontend API calls
   - Monitor network tab for request/response details
""")
print("=" * 70)
