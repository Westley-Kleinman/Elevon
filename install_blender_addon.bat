@echo off
echo Installing TrailPrint3D Blender Addon...
echo.

set "ADDON_FILE=trailprint3d-1-90.py"
set "BLENDER_ADDONS=%APPDATA%\Blender Foundation\Blender\4.4\scripts\addons"

echo Checking if addon file exists...
if not exist "%ADDON_FILE%" (
    echo ERROR: %ADDON_FILE% not found in current directory!
    echo Please make sure the addon file is in the same folder as this batch file.
    pause
    exit /b 1
)

echo Creating Blender addons directory if it doesn't exist...
if not exist "%BLENDER_ADDONS%" (
    mkdir "%BLENDER_ADDONS%"
    echo Created directory: %BLENDER_ADDONS%
)

echo Copying addon to Blender addons folder...
copy "%ADDON_FILE%" "%BLENDER_ADDONS%\"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ SUCCESS! TrailPrint3D addon has been installed.
    echo.
    echo Next steps:
    echo 1. Open Blender
    echo 2. Go to Edit ^> Preferences ^> Add-ons
    echo 3. Search for "TrailPrint3D" and enable it
    echo 4. Press 'N' in the 3D viewport to access the addon panel
    echo.
) else (
    echo.
    echo ❌ ERROR: Failed to copy addon file.
    echo Please try running this as Administrator or install manually.
    echo.
)

pause
