@echo off
cd /d "%~dp0\.."
python -m quantum_rpg gui
if errorlevel 1 (
  echo Install Python 3.10+ and: pip install -r requirements.txt
  pause
)
