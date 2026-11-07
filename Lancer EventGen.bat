@echo off
title EventGen
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Environnement Python introuvable : dossier .venv manquant.
  pause
  exit /b 1
)
echo EventGen demarre. Laissez cette fenetre ouverte, fermez-la pour arreter.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 10; Start-Process 'http://127.0.0.1:8000'"
".venv\Scripts\python.exe" server.py
pause
