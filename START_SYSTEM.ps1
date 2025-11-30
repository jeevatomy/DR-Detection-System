# ============================================================================
# Diabetic Retinopathy Detection System - PowerShell Startup Script
# ============================================================================
# Usage: .\START_SYSTEM.ps1
# This script starts both backend and frontend servers in separate terminals
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  🏥 Diabetic Retinopathy Detection System - Startup Launcher" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$projectRoot = Get-Location

# Check if venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if frontend node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "⚠️  Frontend dependencies not found. Installing..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
}

Write-Host "✅ All dependencies verified!" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Start Backend Server
# ============================================================================
Write-Host "🚀 Starting Backend Server (FastAPI on port 8001)..." -ForegroundColor Cyan

$backendScript = @"
Set-Location '$projectRoot'
. .\venv\Scripts\Activate.ps1
python -m uvicorn src.api:app --host localhost --port 8001
"@

Start-Process -FilePath powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    $backendScript
) -WindowStyle Normal

Start-Sleep -Seconds 2

# ============================================================================
# Start Frontend Server
# ============================================================================
Write-Host "🚀 Starting Frontend Server (React on port 3000)..." -ForegroundColor Cyan

$frontendScript = @"
Set-Location '$projectRoot\frontend'
npm start
"@

Start-Process -FilePath powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    $frontendScript
) -WindowStyle Normal

# ============================================================================
# Startup Complete
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  ✅ STARTUP COMPLETE" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Backend API:  http://localhost:8001" -ForegroundColor Yellow
Write-Host "🖥️  Frontend UI:  http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏳ Waiting for servers to initialize..." -ForegroundColor Cyan
Write-Host "   (First startup takes 15-30 seconds)" -ForegroundColor Cyan
Write-Host ""

# Wait for servers to be ready
$maxRetries = 60
$retryCount = 0
$backendReady = $false
$frontendReady = $false

Write-Host "🔄 Checking server status..." -ForegroundColor Cyan

while ($retryCount -lt $maxRetries -and (-not $backendReady -or -not $frontendReady)) {
    if (-not $backendReady) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "   ✅ Backend API is ready!" -ForegroundColor Green
                $backendReady = $true
            }
        } catch {
            # Backend not ready yet
        }
    }

    if (-not $frontendReady) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Head -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "   ✅ Frontend is ready!" -ForegroundColor Green
                $frontendReady = $true
            }
        } catch {
            # Frontend not ready yet
        }
    }

    if ($backendReady -and $frontendReady) {
        break
    }

    Start-Sleep -Seconds 1
    $retryCount++
    
    if ($retryCount % 5 -eq 0) {
        Write-Host "   ⏳ Waiting... ($retryCount seconds)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  🎉 System is Ready!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

if ($backendReady -and $frontendReady) {
    Write-Host "✅ Both Backend and Frontend are running!" -ForegroundColor Green
    
    # Try to open browser
    try {
        Write-Host ""
        Write-Host "🌐 Opening browser to http://localhost:3000..." -ForegroundColor Cyan
        Start-Process "http://localhost:3000"
    } catch {
        Write-Host "⚠️  Could not open browser. Please manually visit: http://localhost:3000" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Servers are starting but not fully ready yet." -ForegroundColor Yellow
    Write-Host "   Please wait another 10-15 seconds and try http://localhost:3000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 Notes:" -ForegroundColor Cyan
Write-Host "   - Backend logs visible in first terminal window" -ForegroundColor Gray
Write-Host "   - Frontend logs visible in second terminal window" -ForegroundColor Gray
Write-Host "   - First prediction may take ~30 seconds (model initialization)" -ForegroundColor Gray
Write-Host "   - Close either terminal to stop that service" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 API Documentation:" -ForegroundColor Cyan
Write-Host "   - Health: http://localhost:8001/health" -ForegroundColor Gray
Write-Host "   - Model Info: http://localhost:8001/model-info" -ForegroundColor Gray
Write-Host "   - OpenAPI Docs: http://localhost:8001/docs" -ForegroundColor Gray
Write-Host ""

# Keep this window open
Read-Host "Press Enter to exit this launcher window (servers will continue running)"
