@echo off
title Sanctuary V2 Real-Time Backend
cd /d "%~dp0backend"
set "PYTHONPATH=%CD%;%PYTHONPATH%"
C:\Python312\python.exe -u -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
