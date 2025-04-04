@echo off
echo ===== BOT ALBION AVEC DETECTION AUTOMATIQUE =====
echo.
echo Etape 1: Detection du processus Albion Online...
python find_albion.py
echo.
echo Etape 2: Demarrage de l'interface graphique...
echo.
timeout /t 2 > nul
python gui_main.py --force-pid-detection
echo.
pause