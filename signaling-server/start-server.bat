@echo off
echo === WiFi Talker - Сигнальный сервер ===
echo.
echo Запуск сервера на Python...
echo.

cd /d %~dp0
python server.py

pause

