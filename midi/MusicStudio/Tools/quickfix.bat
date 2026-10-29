@echo off
chcp 65001 >nul
title MusicStudio - QuickFix
cd /d "%~dp0.."

echo.
echo   ============================================
echo     MusicStudio - QuickFix / Diagnostics
echo   ============================================
echo.

:: Run environment check
python check_env.py

:: Fix common issues
echo.
echo   --- Quick Fix ---
echo.

:: Check for missing dependencies
python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FIX] Installing numpy...
    python -m pip install numpy
)

python -c "import scipy" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FIX] Installing scipy...
    python -m pip install scipy
)

python -c "import pretty_midi" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FIX] Installing pretty_midi...
    python -m pip install pretty_midi
)

python -c "import soundfile" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FIX] Installing soundfile...
    python -m pip install soundfile
)

:: Create missing directories
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ['Data/Instruments','Data/MIDI','Data/Audio','Output/Exports','Output/Renders','Output/Projects','Output/Stems','SoundFonts','Logs','Config']]"

echo.
echo   ============================================
echo     QuickFix Complete!
echo   ============================================
echo.
echo   If issues persist, try:
echo     - pip install -r requirements.txt --upgrade
echo     - python setup.py
echo.
pause
