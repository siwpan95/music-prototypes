@echo off
chcp 65001 >nul
title 批量处理器
color 0E

:main
cls
echo ========================================
echo       批量处理器
echo ========================================
echo.
echo 功能：
echo   1. 批量转换音频格式
echo   2. 批量应用效果器
echo   3. 批量归一化音频
echo   4. 批量提取片段
echo   5. 批量重命名
echo   6. 返回
echo.
choice /C 123456 /N /M "请选择: "
if errorlevel 6 goto end
if errorlevel 5 goto rename
if errorlevel 4 goto extract
if errorlevel 3 goto normalize
if errorlevel 2 goto effects
if errorlevel 1 goto convert

:convert
cls
echo 批量转换音频格式
echo.
set /p input_dir=输入目录: 
if not exist "%input_dir%" (
    echo 目录不存在
    pause
    goto main
)

set /p pattern=文件模式 (*.wav, *.mp3 等): 
if not defined pattern set pattern=*.wav

set /p output_format=输出格式 (wav/mp3/flac/ogg): 
if not defined output_format set output_format=wav

set /p output_dir=输出目录: 
if not defined output_dir set output_dir=Output\Converted
if not exist "%output_dir%" mkdir "%output_dir%"

echo 正在批量转换...
for %%f in ("%input_dir%\%pattern%") do (
    set filename=%%~nf
    ffmpeg -i "%%f" "%output_dir%\!filename!.%output_format%" -y >nul 2>&1
    echo 已转换: %%f
)
echo 批量转换完成
pause
goto main

:effects
cls
echo 批量应用效果器
echo.
set /p input_dir=输入目录: 
if not exist "%input_dir%" (
    echo 目录不存在
    pause
    goto main
)

set /p pattern=文件模式: 
if not defined pattern set pattern=*.wav

set /p effect=效果器 (1.混响 2.均衡 3.压缩): 
set /p amount=强度 (0.0-1.0): 

set /p output_dir=输出目录: 
if not defined output_dir set output_dir=Output\Processed
if not exist "%output_dir%" mkdir "%output_dir%"

echo 正在批量处理...
for %%f in ("%input_dir%\%pattern%") do (
    set filename=%%~nf
    python -c "
import sys, os
sys.path.append('.')
try:
    from audio_effects import apply_effect
    result = apply_effect('%%f', '$output_dir%/$filename%_fx', $effect, $amount)
    if result:
        print(f'处理完成: {result}')
except Exception as e:
    print(f'处理失败: {e}')
"
)
echo 批量处理完成
pause
goto main

:normalize
cls
echo 批量归一化音频
echo.
set /p input_dir=输入目录: 
if not exist "%input_dir%" (
    echo 目录不存在
    pause
    goto main
)

set /p pattern=文件模式: 
if not defined pattern set pattern=*.wav

set /p target_lufs=目标响度 (-24 到 0, 默认 -16): 
if not defined target_lufs set target_lufs=-16

set /p output_dir=输出目录: 
if not defined output_dir set output_dir=Output\Normalized
if not exist "%output_dir%" mkdir "%output_dir%"

echo 正在批量归一化...
for %%f in ("%input_dir%\%pattern%") do (
    set filename=%%~nf
    ffmpeg -i "%%f" -af "loudnorm=I=!target_lufs!:TP=-1.5:LRA=11" "%output_dir%\!filename!.wav" -y >nul 2>&1
    echo 已归一化: %%f
)
echo 批量归一化完成
pause
goto main

:extract
cls
echo 批量提取音频片段
echo.
set /p input_dir=输入目录: 
if not exist "%input_dir%" (
    echo 目录不存在
    pause
    goto main
)

set /p pattern=文件模式: 
if not defined pattern set pattern=*.wav

set /p start_time=开始时间 (秒): 
if not defined start_time set start_time=0
set /p duration=持续时间 (秒, 0=到结束): 
if not defined duration set duration=0

set /p output_dir=输出目录: 
if not defined output_dir set output_dir=Output\Extracted
if not exist "%output_dir%" mkdir "%output_dir%"

echo 正在批量提取...
for %%f in ("%input_dir%\%pattern%") do (
    set filename=%%~nf
    if "!duration!"=="0" (
        ffmpeg -i "%%f" -ss !start_time! "%output_dir%\!filename!_extract.wav" -y >nul 2>&1
    ) else (
        ffmpeg -i "%%f" -ss !start_time! -t !duration! "%output_dir%\!filename!_extract.wav" -y >nul 2>&1
    )
    echo 已提取: %%f
)
echo 批量提取完成
pause
goto main

:rename
cls
echo 批量重命名文件
echo.
set /p input_dir=输入目录: 
if not exist "%input_dir%" (
    echo 目录不存在
    pause
    goto main
)

set /p pattern=文件模式: 
if not defined pattern set pattern=*.wav

set /p prefix=文件名前缀: 
if not defined prefix set prefix=audio_
set /p start_num=起始编号: 
if not defined start_num set start_num=1

set /p output_dir=输出目录: 
if not defined output_dir set output_dir=Output\Renamed
if not exist "%output_dir%" mkdir "%output_dir%"

echo 正在批量重命名...
setlocal enabledelayedexpansion
set count=!start_num!
for %%f in ("%input_dir%\%pattern%") do (
    set num=0000!count!
    set num=!num:~-4!
    copy "%%f" "%output_dir%\!prefix%!num!.wav" >nul
    echo 已重命名: %%f -^> !prefix%!num!.wav
    set /a count+=1
)
endlocal
echo 批量重命名完成
pause
goto main

:end
exit