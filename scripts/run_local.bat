@echo off
REM Start the local backend using conda run so activation isn't required in the current shell
REM Usage: from repo root: scripts\run_local.bat

SET CONDA_EXE=%USERPROFILE%\Miniconda3\Scripts\conda.exe
IF NOT EXIST "%CONDA_EXE%" (
  SET CONDA_EXE=%USERPROFILE%\Anaconda3\Scripts\conda.exe
)

IF EXIST "%CONDA_EXE%" (
  echo Starting uvicorn using conda run -n asia_02 ...
  "%CONDA_EXE%" run -n asia_02 --no-capture-output uvicorn backend.app:app --reload --port 8001
) ELSE (
  echo Could not find conda.exe at %CONDA_EXE%. Ensure conda is installed and on PATH, or activate your env manually:
  echo     conda activate asia_02
  echo Then run:
  echo     uvicorn backend.app:app --reload --port 8001
)
