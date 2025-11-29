@echo off
REM Stop the local uvicorn server by finding the PID listening on 8002 or 8004 and killing it.
SETLOCAL ENABLEDELAYEDEXPANSION

REM Try port 8002 first
set PID=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002"') do set PID=%%a

if "%PID%"=="" (
  REM try port 8004
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8004"') do set PID=%%a
)

if "%PID%"=="" (
  echo No process found listening on ports 8002 or 8004.
  echo If you started uvicorn in a console, switch to that console and press Ctrl+C to stop it.
  exit /b 0
)

echo Found PID %PID% - attempting to stop it...
taskkill /PID %PID% /F
if %ERRORLEVEL%==0 (
  echo Stopped PID %PID%.
) else (
  echo Failed to stop PID %PID%. You may need to run this as Administrator.
)
ENDLOCAL
