@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
set "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,10.0.2.2"

if not exist "venv\Scripts\python.exe" (
  echo [NOVA] Python virtual environment was not found.
  echo Create the venv and install apps\backend\requirements.txt first.
  exit /b 1
)

venv\Scripts\python.exe apps\backend\manage.py migrate || exit /b 1
venv\Scripts\python.exe apps\backend\manage.py seed_demo || exit /b 1
venv\Scripts\python.exe apps\backend\manage.py runserver 0.0.0.0:8000
