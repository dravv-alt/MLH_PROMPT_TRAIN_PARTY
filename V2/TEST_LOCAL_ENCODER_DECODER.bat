@echo off
setlocal
cd /d "%~dp0backend"

if exist ".venv_nlp\Scripts\python.exe" (
  ".venv_nlp\Scripts\python.exe" scripts\local_encoder_decoder_cli.py %*
) else if exist "C:\Python312\python.exe" (
  "C:\Python312\python.exe" scripts\local_encoder_decoder_cli.py %*
) else (
  py -3.12 scripts\local_encoder_decoder_cli.py %*
)

set "SANCTUARY_TEST_EXIT=%ERRORLEVEL%"
endlocal & exit /b %SANCTUARY_TEST_EXIT%
