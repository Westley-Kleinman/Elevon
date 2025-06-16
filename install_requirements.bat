@echo off
echo Installing Python packages for the Flask application...

REM Set Python path for this session
set PATH=%PATH%;C:\Users\westk\AppData\Local\Programs\Python\Python311\;C:\Users\westk\AppData\Local\Programs\Python\Python311\Scripts\

REM Navigate to the Flask app directory
cd /d "C:\Elevon\image-filter-web"

REM Install requirements
python -m pip install -r requirements.txt

echo.
echo Installation complete! You can now run the Flask app using run_flask_app.bat
pause
