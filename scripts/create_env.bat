@echo off
REM Create and populate the conda environment asia_02 for this project
REM Usage: open Anaconda Prompt or a cmd with conda on PATH, then run this script

echo Creating conda environment asia_02 with Python 3.11...
conda create -n asia_02 python=3.11 -y

echo Activating asia_02 and installing Python dependencies...
call conda activate asia_02

IF EXIST "backend\requirements.txt" (
    echo Installing backend requirements...
    pip install -r backend\requirements.txt
) ELSE (
    echo No backend requirements file found at backend\requirements.txt
)

IF EXIST "python_code\requirements.txt" (
    echo Installing python_code requirements...
    pip install -r python_code\requirements.txt
) ELSE (
    echo No python_code requirements file found at python_code\requirements.txt
)

echo Done. To use the environment:
echo     conda activate asia_02
echo Start the backend: uvicorn backend.app:app --reload --port 8001
pause
