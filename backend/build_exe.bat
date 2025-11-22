@echo off
echo === Creazione eseguibile portabile ===
pip install -r requirements.txt
python -m PyInstaller --onefile main.py
echo.
echo Fatto! Il file eseguibile si trova in dist\main.exe
pause