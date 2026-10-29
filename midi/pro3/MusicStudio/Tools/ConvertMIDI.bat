@echo off
chcp 65001 >nul
title MIDI转换工具
color 0A

if "%~1"=="" (
    set /p input=请输入MIDI文件路径: 
) else (
    set input=%~1
)

if not exist "%input%" (
    echo 文件不存在: %input%
    pause
    exit /b 1
)

:format_menu
cls
echo 转换选项:
echo   1. MIDI 转 WAV
echo   2. MIDI 转 MP3
echo   3. MIDI 转 FLAC
echo   4. 批量转换目录
echo.
set /p format=选择格式: 

if "%format%"=="4" goto batch

if not defined output (
    set output=%~dpn1
)

if "%format%"=="1" set ext=wav
if "%format%"=="2" set ext=mp3
if "%format%"=="3" set ext=flac

echo 正在转换...
python -c "
import sys, os
sys.path.append('.')
try:
    from convert_tools import midi_to_audio
    result = midi_to_audio('$input%', '$output%.$ext%')
    if result:
        print(f'转换完成: {result}')
    else:
        print('转换失败')
        sys.exit(1)
except Exception as e:
    print(f'转换失败: {e}')
    sys.exit(1)
"

if %errorlevel% equ 0 (
    echo 转换成功: %output%.%ext%
) else (
    echo 转换失败
)
pause
exit /b

:batch
set /p folder=请输入目录路径: 
if not exist "%folder%" (
    echo 目录不存在
    pause
    exit /b
)

set /p ext=输出格式 (wav/mp3/flac): 
set /p pattern=文件模式 (*.mid): 
if not defined pattern set pattern=*.mid

echo 批量转换中...
for %%f in ("%folder%\%pattern%") do (
    call :ConvertSingle "%%f" "%ext%"
)
echo 批量转换完成
pause
exit /b

:ConvertSingle
set file=%~1
set ext=%~2
set output=%~dpn1.%ext%

python -c "
import sys, os
sys.path.append('.')
try:
    from convert_tools import midi_to_audio
    result = midi_to_audio('$file%', '$output%')
    if result:
        print(f'转换完成: {result}')
except Exception as e:
    print(f'转换失败: {e}')
"
exit /b