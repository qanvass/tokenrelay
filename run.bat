@echo off
title TokenOpt: Universal LLM Cost Savings Agent & Control Center
echo ==============================================================
echo Launching TokenOpt Interactive Control Center...
echo ==============================================================
echo 1. Launch Interactive Web Dashboard
echo 2. Run System Auto-Doctor Scan
echo 3. Synchronize All IDE Rules
echo 4. Exit
echo.
set /p choice="Select an option (1-4) [default: 1]: "
if "%choice%"=="2" goto doctor
if "%choice%"=="3" goto sync
if "%choice%"=="4" goto end

:dashboard
python agent.py dashboard
goto end

:doctor
python agent.py doctor
echo.
pause
goto end

:sync
python agent.py sync
echo.
pause
goto end

:end
