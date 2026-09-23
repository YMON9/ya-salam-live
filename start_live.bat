@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
echo.
echo   يا سلام لايف تعمل الآن على:
echo   http://127.0.0.1:8000
echo.
.venv\Scripts\python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause
