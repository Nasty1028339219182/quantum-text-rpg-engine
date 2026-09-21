@echo off
cd /d "%~dp0\.."
python -m quantum_rpg validate %1
pause
