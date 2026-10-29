@echo off
chcp 65001 >nul
title MusicStudio v4.0
cls

:: ═══════════════════════════════════════════════════
:: MusicStudio - Windows 启动器
:: 来源: Pro3 MusicStudio.bat + Pro4 MusicStudioPro.bat
:: ═══════════════════════════════════════════════════

echo.
echo   ============================================
echo     MusicStudio v4.0
echo     四合一音乐制作系统
echo   ============================================
echo.
echo     [1] DAW GUI
echo     [2] Batch (All 5 Moods)
echo     [3] Interactive CLI
echo     [4] Quick Demo (happy)
echo     [5] Environment Check
echo     [6] Setup / Install Deps
echo     [Q] Quit
echo.
echo   ============================================

choice /c 123456Q /n /m "  Select: "

if errorlevel 7 goto quit
if errorlevel 6 goto setup
if errorlevel 5 goto env
if errorlevel 4 goto demo
if errorlevel 3 goto cli
if errorlevel 2 goto batch
if errorlevel 1 goto gui

:gui
    echo.
    echo   Starting DAW GUI...
    python main.py --mode gui
    goto end

:batch
    echo.
    echo   Running batch for all 5 moods...
    python main.py --mode batch --mood happy --bars 4 --output Output/Exports/happy_demo.wav
    python main.py --mode batch --mood sad --bars 4 --output Output/Exports/sad_demo.wav
    python main.py --mode batch --mood epic --bars 4 --output Output/Exports/epic_demo.wav
    python main.py --mode batch --mood calm --bars 4 --output Output/Exports/calm_demo.wav
    python main.py --mode batch --mood tense --bars 4 --output Output/Exports/tense_demo.wav
    echo.
    echo   All done! Output in Output/Exports/
    goto end

:cli
    echo.
    python main.py --mode cli
    goto end

:demo
    echo.
    echo   Generating quick demo (happy, 8 bars)...
    python main.py --mode batch --mood happy --bars 8 --output Output/Exports/quick_demo.wav
    echo.
    echo   Done! Output/Exports/quick_demo.wav
    goto end

:env
    echo.
    python check_env.py
    goto end

:setup
    echo.
    python setup.py
    goto end

:quit
    echo   Goodbye!
    exit /b 0

:end
    echo.
    echo   Press any key to return to menu...
    pause >nul
    cls
    goto :EOF
