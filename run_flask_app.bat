@echo off
REM Set Python path for this session
set PATH=%PATH%;C:\Users\westk\AppData\Local\Programs\Python\Python311\;C:\Users\westk\AppData\Local\Programs\Python\Python311\Scripts\

REM Navigate to the Flask app directory
cd /d "C:\Elevon\image-filter-web"

REM Run the Flask application
python app.py

pause
