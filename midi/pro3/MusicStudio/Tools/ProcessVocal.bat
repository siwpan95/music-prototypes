@echo off
chcp 65001 >nul
title 人声处理器
color 0E

:main
cls
echo ========================================
echo       人声处理器
echo ========================================
echo.
if not exist "Data\Audio\*.wav" if not exist "Data\Audio\*.mp3" (
    echo 音频目录为空
    echo 请将人声音频文件放在 Data\Audio\ 目录
    pause
    exit /b
)

dir "Data\Audio\*.wav" "Data\Audio\*.mp3" /b
echo.
set /p vocal_file=选择人声音频文件: 
if not exist "Data\Audio\%vocal_file%" (
    echo 文件不存在
    pause
    goto main
)

echo 人声处理功能:
echo   1. 音高校正 (Auto-Tune)
echo   2. 和声生成
echo   3. 混响效果
echo   4. 压缩处理
echo   5. 节奏校正
echo   6. 去除噪声
echo   7. 全部处理
echo.
set /p process=选择处理功能: 

set /p output_name=输出文件名: 
if not defined output_name set output_name=processed_vocal

:processing
echo 正在处理人声...

if "%process%"=="1" (
    set pitch_correction=0.7
    set /p pitch_correction=音高校正强度 (0.0-1.0, 默认0.7): 
    python -c "
from vocal_processor import pitch_correct
result = pitch_correct('Data\Audio\%vocal_file%', '$output_name', $pitch_correction)
print(f'音高校正完成: {result}')
"
)

if "%process%"=="2" (
    set harmony_voices=3
    set /p harmony_voices=和声数量 (1-8, 默认3): 
    python -c "
from vocal_processor import generate_harmony
result = generate_harmony('Data\Audio\%vocal_file%', '$output_name', $harmony_voices)
print(f'和声生成完成: {result}')
"
)

if "%process%"=="3" (
    set reverb_amount=0.3
    set /p reverb_amount=混响强度 (0.0-1.0, 默认0.3): 
    python -c "
from vocal_processor import add_reverb
result = add_reverb('Data\Audio\%vocal_file%', '$output_name', $reverb_amount)
print(f'混响添加完成: {result}')
"
)

if "%process%"=="4" (
    set compression=0.5
    set /p compression=压缩强度 (0.0-1.0, 默认0.5): 
    python -c "
from vocal_processor import apply_compression
result = apply_compression('Data\Audio\%vocal_file%', '$output_name', $compression)
print(f'压缩处理完成: {result}')
"
)

if "%process%"=="5" (
    set /p tempo=目标曲速 (BPM): 
    python -c "
from vocal_processor import time_stretch
result = time_stretch('Data\Audio\%vocal_file%', '$output_name', $tempo)
print(f'节奏校正完成: {result}')
"
)

if "%process%"=="6" (
    set noise_reduction=0.3
    set /p noise_reduction=降噪强度 (0.0-1.0, 默认0.3): 
    python -c "
from vocal_processor import reduce_noise
result = reduce_noise('Data\Audio\%vocal_file%', '$output_name', $noise_reduction)
print(f'降噪处理完成: {result}')
"
)

if "%process%"=="7" (
    echo 执行完整处理流程...
    python -c "
from vocal_processor import process_vocal
result = process_vocal('Data\Audio\%vocal_file%', '$output_name')
print(f'完整处理完成: {result}')
"
)

if exist "Data\Audio\%output_name%.wav" (
    echo 处理完成: Data\Audio\%output_name%.wav
) else (
    echo 处理失败
)

pause
goto main