@echo off
title Autonomous Stock Live Web Terminal
echo ==============================================================
echo Launching Live Stock Trading Terminal (Auto-reloads every 2s)
echo URL: http://localhost:9012
echo ==============================================================
python "%~dp0web_app\server.py"
pause
