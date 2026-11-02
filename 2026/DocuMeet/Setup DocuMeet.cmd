@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
if errorlevel 1 (
  echo Setup did not finish. See the error above.
) else (
  echo Setup complete. Open Launch DocuMeet.cmd and download the offline models.
)
pause
