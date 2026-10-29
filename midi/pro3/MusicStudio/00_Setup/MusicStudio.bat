@echo off
chcp 65001 >nul
title 音乐制作工作室
color 0F

:menu
cls
echo ========================================
echo       音乐制作工作室 v2.0
echo ========================================
echo.
echo   [1] 参数生成器
echo   [2] MIDI生成器
echo   [3] 音频混合器
echo   [4] 人声处理器
echo   [5] 采样管理器
echo   [6] 项目编译器
echo   [7] 批量处理器
echo   [8] 设置
echo   [0] 退出
echo.
echo ========================================

choice /C 123456780 /N /M "请选择功能: "
if errorlevel 9 goto exit
if errorlevel 8 goto settings
if errorlevel 7 goto batch
if errorlevel 6 goto compiler
if errorlevel 5 goto sampler
if errorlevel 4 goto vocal
if errorlevel 3 goto mixer
if errorlevel 2 goto midi
if errorlevel 1 goto param

:param
cls
echo 启动参数生成器...
cd /d "01_ParamGen"
start ParamGen.bat
cd ..
pause
goto menu

:midi
cls
echo 启动MIDI生成器...
cd /d "02_MIDIGen"
start MIDIGen.bat
cd ..
pause
goto menu

:mixer
cls
echo 启动音频混合器...
cd /d "03_AudioMix"
start AudioMix.bat
cd ..
pause
goto menu

:vocal
cls
echo 启动人声处理器...
start Tools\ProcessVocal.bat
pause
goto menu

:sampler
cls
echo 启动采样管理器...
start Tools\SamplerTool.bat
pause
goto menu

:compiler
cls
echo 启动项目编译器...
call :RunPythonScript "Tools\ProjectCompiler.py"
pause
goto menu

:batch
cls
echo 启动批量处理器...
start Tools\BatchProcess.bat
pause
goto menu

:settings
cls
echo 系统设置
echo.
echo [1] 配置音频设备
echo [2] 设置音色库路径
echo [3] 更改输出目录
echo [4] 恢复默认设置
echo [5] 返回
echo.
choice /C 12345 /N /M "请选择: "
if errorlevel 5 goto menu
if errorlevel 4 goto reset
if errorlevel 3 goto output
if errorlevel 2 goto soundfont
if errorlevel 1 goto audio

:audio
cls
echo 配置音频设备...
powershell -ExecutionPolicy Bypass -File "Tools\ConfigAudio.ps1"
pause
goto settings

:soundfont
cls
set /p sfpath=请输入音色库路径: 
if exist "%sfpath%" (
    echo SoundFont=%sfpath% > "Config\Defaults.ini.tmp"
    findstr /V "SoundFont" "Config\Defaults.ini" >> "Config\Defaults.ini.tmp"
    move /y "Config\Defaults.ini.tmp" "Config\Defaults.ini"
    echo 音色库路径已更新
) else (
    echo 路径不存在
)
pause
goto settings

:output
cls
set /p outpath=请输入输出目录: 
if not exist "%outpath%" mkdir "%outpath%"
if exist "%outpath%" (
    echo OutputPath=%outpath% > "Config\Defaults.ini.tmp"
    findstr /V "OutputPath" "Config\Defaults.ini" >> "Config\Defaults.ini.tmp"
    move /y "Config\Defaults.ini.tmp" "Config\Defaults.ini"
    echo 输出目录已更新
)
pause
goto settings

:reset
cls
echo 正在恢复默认设置...
if exist "Config\Defaults.ini.bak" del "Config\Defaults.ini.bak"
if exist "Config\Defaults.ini" (
    copy "Config\Defaults.ini" "Config\Defaults.ini.bak"
    del "Config\Defaults.ini"
)
echo [System] > "Config\Defaults.ini"
echo SampleRate=44100 >> "Config\Defaults.ini"
echo Channels=2 >> "Config\Defaults.ini"
echo BufferSize=2048 >> "Config\Defaults.ini"
echo. >> "Config\Defaults.ini"
echo [Audio] >> "Config\Defaults.ini"
echo SoundFont=default.sf2 >> "Config\Defaults.ini"
echo NormalizeOutput=true >> "Config\Defaults.ini"
echo 默认设置已恢复
pause
goto menu

:exit
cls
color 0F
echo 感谢使用音乐制作工作室！
timeout /t 2 /nobreak >nul
exit

:RunPythonScript
set PY_SCRIPT=%~1
python "%PY_SCRIPT%"
exit /b