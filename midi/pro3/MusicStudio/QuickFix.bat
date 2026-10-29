@echo off
chcp 65001 >nul
title 故障排除工具
color 0C

:menu
cls
echo ========================================
echo       故障排除工具
echo ========================================
echo.
echo 常见问题解决：
echo   1. 音频无法播放
echo   2. MIDI无法生成
echo   3. Python错误
echo   4. 文件路径问题
echo   5. 清理临时文件
echo   6. 重置配置
echo   7. 检查依赖
echo   8. 返回
echo.
choice /C 12345678 /N /M "请选择: "
if errorlevel 8 goto end
if errorlevel 7 goto check
if errorlevel 6 goto reset
if errorlevel 5 goto clean
if errorlevel 4 goto path
if errorlevel 3 goto python
if errorlevel 2 goto midi
if errorlevel 1 goto audio

:audio
cls
echo 修复音频问题
echo.
echo 1. 检查默认音频设备
powershell Get-WmiObject Win32_SoundDevice
echo.
echo 2. 测试音频输出
python -c "import winsound; winsound.Beep(1000, 500)"
echo.
echo 3. 重置音频设置
reg delete "HKCU\Software\Microsoft\Multimedia\Audio" /f
echo 音频设置已重置
pause
goto menu

:midi
cls
echo 修复MIDI问题
echo.
echo 检查MIDI驱动程序...
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\MCI" /v "Sequencer"
echo.
echo 重新注册MIDI组件...
regsvr32 /s midimap.dll
regsvr32 /s mciseq.dll
echo MIDI组件已重新注册
pause
goto menu

:python
cls
echo 修复Python问题
echo.
python --version
echo.
echo 重新安装Python包...
pip install --upgrade pip
pip install --force-reinstall numpy pygame
echo Python包已重新安装
pause
goto menu

:path
cls
echo 修复路径问题
echo.
echo 当前路径: %CD%
echo.
echo 修复文件关联...
assoc .mid=MIDIFile
ftype MIDIFile=%%SystemRoot%%\system32\mplay32.exe /play /close "%%1"
assoc .json=jsonfile
ftype jsonfile=notepad.exe "%%1"
echo 文件关联已修复
pause
goto menu

:clean
cls
echo 清理临时文件
echo.
echo 清理临时目录...
del /q /f "Temp\*.*" 2>nul
del /q /f "Output\Temp\*.*" 2>nul
echo 清理日志文件...
del /q /f "Logs\*.log" 2>nul
echo 清理完成
pause
goto menu

:reset
cls
echo 重置系统配置
echo.
echo 注意：这将恢复所有设置为默认值
echo 但不会删除您的项目文件。
echo.
set /p confirm=确定要重置吗？(Y/N): 
if /i "!confirm!"=="Y" (
    echo 正在重置...
    if exist "Config\Studio.ini.bak" del "Config\Studio.ini.bak"
    if exist "Config\Studio.ini" (
        copy "Config\Studio.ini" "Config\Studio.ini.bak"
        del "Config\Studio.ini"
    )
    call GenerateConfig.bat
    echo 系统配置已重置
)
pause
goto menu

:check
cls
echo 检查系统依赖
echo.
echo 1. 检查Python...
python --version
if %errorlevel% neq 0 (
    echo Python未安装或配置错误
) else (
    echo Python正常
)
echo.
echo 2. 检查FFmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg未找到
) else (
    ffmpeg -version | findstr "version"
    echo FFmpeg正常
)
echo.
echo 3. 检查音色库...
if exist "Libs\SoundFonts\*.sf2" (
    echo 音色库已安装
) else (
    echo 音色库未找到
)
echo.
echo 4. 检查Python包...
echo 正在检查numpy...
python -c "import numpy; print('numpy版本:', numpy.__version__)"
echo 正在检查pygame...
python -c "import pygame; print('pygame版本:', pygame.ver)"
echo 正在检查pretty_midi...
python -c "import pretty_midi; print('pretty_midi版本:', pretty_midi.__version__)"
echo 正在检查soundfile...
python -c "import soundfile; print('soundfile版本:', soundfile.__version__)"
echo.
echo 依赖检查完成
pause
goto menu

:end
exit