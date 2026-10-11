@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 ( echo Dependency installation failed & pause & exit /b 1 )
set /p GEMINI_API_KEY=Enter your Gemini API key (input visible): 
if "%GEMINI_API_KEY%"=="" ( echo No key: AI scanner will show service unavailable. )
python backend\app.py
pause
