@echo off
REM Start uvicorn in a new window using the python.exe from the asia_02 conda env.
SET PY1=%USERPROFILE%\Miniconda3\envs\asia_02\python.exe
SET PY2=%USERPROFILE%\Anaconda3\envs\asia_02\python.exe

if exist "%PY1%" (
  start "Asia's Panel" "%PY1%" -m uvicorn backend.app:app --port 8002 --host 127.0.0.1
  goto :eof
)
if exist "%PY2%" (
  start "Asia's Panel" "%PY2%" -m uvicorn backend.app:app --port 8002 --host 127.0.0.1
  goto :eof
)
echo Could not find python in the asia_02 env. Run scripts\create_env.bat first.
exit /b 2
