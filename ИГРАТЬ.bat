@echo off
cd /d "%~dp0"
python -m quantum_rpg gui
if errorlevel 1 (
  echo.
  echo Нужен Python 3.10 или новее.
  echo 1. Установи его с https://www.python.org и отметь Add python.exe to PATH
  echo 2. В этой папке выполни: pip install -r requirements.txt
  echo 3. Снова запусти ИГРАТЬ.bat
  echo.
  echo Либо скачай QuantumRPG.exe из того же релиза. Это и есть окно.
  echo Игры уже внутри: выбери в списке и нажми Играть. Редактор там же.
  echo.
  pause
)
