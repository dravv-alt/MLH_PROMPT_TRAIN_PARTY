@echo off
cd /d "%~dp0backend"
set "PYTHONPATH=%CD%;%CD%\.testdeps;%PYTHONPATH%"
if exist ".venv_nlp\Scripts\python.exe" (
  .venv_nlp\Scripts\python.exe scripts\setup_semantic_resources.py
) else (
  python scripts\setup_semantic_resources.py
)
pause
