@echo off
title Sanctuary V2 Interactive Terminal
cd /d "%~dp0backend"
set "PYTHONPATH=%CD%;%PYTHONPATH%"
C:\Python312\python.exe interactive_chat.py --realizer hosted
pause
