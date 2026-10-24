@echo off
cd /d "%~dp0backend"
set "PYTHONPATH=%CD%;%CD%\.testdeps;%PYTHONPATH%"
if exist ".venv_nlp\Scripts\python.exe" (
  .venv_nlp\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
) else (
  python -m uvicorn main:app --host 127.0.0.1 --port 8000
)
pause
