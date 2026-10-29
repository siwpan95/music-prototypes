@echo off
chcp 65001 >nul
title MusicStudio - Install
cd /d "%~dp0.."

echo.
echo   ============================================
echo     MusicStudio - Installation
echo   ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python not found! Please install Python 3.8+
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   [OK] Python found

:: Install dependencies
echo.
echo   Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo   [WARN] Some packages may have failed
    echo   Try: python -m pip install --upgrade pip
)

:: Create desktop shortcut
echo.
echo   Creating directories...
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ['Data/Instruments','Data/MIDI','Data/Audio','Output/Exports','Output/Renders','SoundFonts','Logs']]"

echo.
echo   ============================================
echo     Installation Complete!
echo   ============================================
echo.
echo   Quick Start:
echo     - Run MusicStudio.bat
echo     - Or: python main.py
echo.
echo   For better audio quality:
echo     Download FluidR3_GM.sf2 to SoundFonts/
echo.
pause
