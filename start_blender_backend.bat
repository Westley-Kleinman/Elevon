@echo off
echo Starting Elevon Blender GPX Preview Backend...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python 3.8 or later.
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import flask, flask_cors" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required Python packages...
    pip install flask flask-cors
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Check if Blender is available
echo Checking Blender availability...
python -c "from blender_gpx_preview import BlenderGPXPreview; BlenderGPXPreview()" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Blender not found. Backend will run but high-quality rendering will be unavailable.
    echo Please install Blender 4.2+ for full functionality.
    echo.
)

echo Starting Flask backend on http://localhost:5000...
echo Press Ctrl+C to stop the server.
echo.

REM Start the Flask backend
python blender_backend.py

pause
