@echo off
cd /d "%~dp0"
set "PYTHONPATH=%CD%\backend;%CD%\backend\.testdeps;%PYTHONPATH%"
if exist "backend\.venv_nlp\Scripts\python.exe" (
  backend\.venv_nlp\Scripts\python.exe backend\scripts\submission_demo.py --serve
) else (
  python backend\scripts\submission_demo.py --serve
)
pause
