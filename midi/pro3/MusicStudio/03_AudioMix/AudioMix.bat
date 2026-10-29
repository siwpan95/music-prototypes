@echo off
chcp 65001 >nul
title 音频混合器
color 0D

:main
cls
echo ========================================
echo       音频混合器
echo ========================================
echo.
echo 功能：
echo   1. 从MIDI生成音频
echo   2. 混合多个音频
echo   3. 应用效果器
echo   4. 导出最终混音
echo   5. 批量渲染
echo   6. 返回
echo.
choice /C 123456 /N /M "请选择: "
if errorlevel 6 goto end
if errorlevel 5 goto batch
if errorlevel 4 goto export
if errorlevel 3 goto effects
if errorlevel 2 goto mix
if errorlevel 1 goto synth

:synth
cls
echo 从MIDI合成音频
echo.
if not exist "Data\MIDI\*.mid" if not exist "Data\MIDI\*.midi" (
    echo 没有找到MIDI文件
    pause
    goto main
)

dir "Data\MIDI\*.mid" "Data\MIDI\*.midi" /b
echo.
set /p midi_file=选择MIDI文件: 
if not exist "Data\MIDI\%midi_file%" (
    echo 文件不存在
    pause
    goto main
)

set /p output_name=输出文件名: 
if not defined output_name set output_name=%midi_file:~0,-4%

set /p use_soundfont=使用SoundFont音色库? (Y/N, 默认Y): 
if /i "%use_soundfont%"=="N" (
    set soundfont_arg=
) else (
    if exist "Libs\SoundFonts\default.sf2" (
        set soundfont_arg="-soundfont Libs\SoundFonts\default.sf2"
    ) else (
        echo 警告: 未找到音色库
        set soundfont_arg=
    )
)

echo 正在合成音频...
python -c "
import sys, os
sys.path.append('.')
try:
    from midi_utils import synthesize_midi
    result = synthesize_midi('Data\MIDI\%midi_file%', '$output_name', $soundfont_arg%)
    if result:
        print(f'音频已保存: {result}')
    else:
        print('合成失败')
        sys.exit(1)
except Exception as e:
    print(f'合成失败: {e}')
    sys.exit(1)
"

if %errorlevel% equ 0 (
    echo 音频合成完成
) else (
    echo 合成失败
)
pause
goto main

:mix
cls
echo 混合多个音频
echo.
if not exist "Data\Audio\*.wav" if not exist "Data\Audio\*.mp3" (
    echo 没有找到音频文件
    pause
    goto main
)

dir "Data\Audio\*.wav" "Data\Audio\*.mp3" /b
echo.
set /p audio_files=选择音频文件（用空格分隔）: 
if not defined audio_files (
    echo 没有选择文件
    pause
    goto main
)

set /p output_name=输出文件名: 
if not defined output_name set output_name=mixdown

set /p volumes=设置音量（用空格分隔，如: 1.0 0.8 0.5）: 
if not defined volumes (
    set volume_arg=
) else (
    set volume_arg="-volumes %volumes%"
)

echo 正在混合音频...
powershell -ExecutionPolicy Bypass -File "AudioMix.ps1" -Action Mix -Files "%audio_files%" -Output "%output_name%" %volume_arg%

if exist "Output\Renders\%output_name%.wav" (
    echo 混合完成: Output\Renders\%output_name%.wav
) else (
    echo 混合失败
)
pause
goto main

:effects
cls
echo 应用效果器
echo.
if not exist "Data\Audio\*.wav" if not exist "Data\Audio\*.mp3" (
    echo 没有找到音频文件
    pause
    goto main
)

dir "Data\Audio\*.wav" "Data\Audio\*.mp3" /b
echo.
set /p audio_file=选择音频文件: 
if not exist "Data\Audio\%audio_file%" (
    echo 文件不存在
    pause
    goto main
)

echo 可用效果器：
echo   1. 混响
echo   2. 均衡器
echo   3. 压缩器
echo   4. 延迟
echo   5. 合唱
echo.
set /p effect=选择效果器: 
set /p amount=强度 (0.0-1.0): 

set /p output_name=输出文件名: 
if not defined output_name set output_name=%audio_file:~0,-4%_fx

echo 正在应用效果器...
python -c "
import sys, os
sys.path.append('.')
try:
    from audio_effects import apply_effect
    result = apply_effect('Data\Audio\%audio_file%', '$output_name', $effect, $amount)
    if result:
        print(f'处理完成: {result}')
    else:
        print('处理失败')
        sys.exit(1)
except Exception as e:
    print(f'处理失败: {e}')
    sys.exit(1)
"

if %errorlevel% equ 0 (
    echo 效果器应用完成
) else (
    echo 处理失败
)
pause
goto main

:export
cls
echo 导出最终混音
echo.
if not exist "Output\Renders\*.wav" (
    echo 没有找到混音文件
    pause
    goto main
)

dir "Output\Renders\*.wav" /b
echo.
set /p mix_file=选择混音文件: 
if not exist "Output\Renders\%mix_file%" (
    echo 文件不存在
    pause
    goto main
)

set /p format=输出格式 (1.WAV 2.MP3 3.FLAC): 
if "%format%"=="1" set ext=wav
if "%format%"=="2" set ext=mp3
if "%format%"=="3" set ext=flac

set /p output_name=输出文件名: 
if not defined output_name set output_name=%mix_file:~0,-4%

echo 正在导出...
if "%format%"=="2" (
    ffmpeg -i "Output\Renders\%mix_file%" -codec:a libmp3lame -qscale:a 2 "Output\Exports\%output_name%.mp3" -y
) else (
    copy "Output\Renders\%mix_file%" "Output\Exports\%output_name%.%ext%"
)

if exist "Output\Exports\%output_name%.%ext%" (
    echo 导出完成: Output\Exports\%output_name%.%ext%
) else (
    echo 导出失败
)
pause
goto main

:batch
cls
echo 批量渲染
echo.
set /p input_dir=输入目录: 
if not exist "%input_dir%" (
    echo 目录不存在
    pause
    goto main
)

set /p pattern=文件模式 (*.mid, *.json 等): 
if not defined pattern set pattern=*.mid

set /p output_dir=输出目录: 
if not defined output_dir set output_dir=Output\Batch
if not exist "%output_dir%" mkdir "%output_dir%"

echo 正在批量处理...
for %%f in ("%input_dir%\%pattern%") do (
    echo 处理: %%f
    python -c "
import sys, os
sys.path.append('.')
try:
    from batch_processor import process_file
    result = process_file('%%f', '%output_dir%')
    if result:
        print(f'处理完成: {result}')
except Exception as e:
    print(f'处理失败: {e}')
"
)

echo 批量处理完成
pause
goto main

:end
exit