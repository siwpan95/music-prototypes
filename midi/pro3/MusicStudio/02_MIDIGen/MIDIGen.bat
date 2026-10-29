@echo off
chcp 65001 >nul
title MIDI生成器
color 0C

:main
cls
echo ========================================
echo       MIDI生成器
echo ========================================
echo.
if not exist "Data\Instruments\*.json" (
    echo 没有找到乐器配置文件
    echo 请先运行参数生成器
    pause
    exit /b
)

echo 可用的乐器配置:
dir "Data\Instruments\*.json" /b
echo.

:select_files
set /p files=选择配置文件（用逗号分隔，或输入 all 选择全部）: 
if "%files%"=="all" (
    set file_list=
    for %%f in ("Data\Instruments\*.json") do (
        set file_list=!file_list! "%%f"
    )
) else (
    set file_list=
    for %%f in (%files%) do (
        if exist "Data\Instruments\%%f" (
            set file_list=!file_list! "Data\Instruments\%%f"
        ) else if exist "Data\Instruments\%%f.json" (
            set file_list=!file_list! "Data\Instruments\%%f.json"
        )
    )
)

if not defined file_list (
    echo 没有找到选择的文件
    pause
    goto select_files
)

:settings
set /p tempo=曲速 (BPM, 默认120): 
if not defined tempo set tempo=120
set /p time_sig=拍号 (格式: 4/4, 默认4/4): 
if not defined time_sig set time_sig=4/4
set /p output_name=输出名称: 
if not defined output_name set output_name=song

:process
echo 正在生成MIDI...
python -c "
import sys, os, json
sys.path.append('.')
try:
    from midi_utils import create_midi_from_json
    files = [$file_list]
    create_midi_from_json(files, '$output_name', $tempo, '$time_sig')
    print('MIDI生成完成')
except Exception as e:
    print(f'生成失败: {e}')
    sys.exit(1)
"

if %errorlevel% equ 0 (
    echo MIDI已保存: Data\MIDI\%output_name%.mid
) else (
    echo MIDI生成失败
)
pause
goto main