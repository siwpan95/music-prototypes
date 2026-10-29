@echo off
chcp 65001 >nul
title 创建快捷方式
color 0A

echo 创建桌面快捷方式...
echo.

:: 获取桌面路径
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v "Desktop"') do set desktop=%%b
set desktop=%desktop:%%USERPROFILE%%=%USERPROFILE%%

:: 创建主程序快捷方式
echo [InternetShortcut] > "%desktop%\音乐制作工作室.url"
echo URL="file:///%CD%\MusicStudio.bat" >> "%desktop%\音乐制作工作室.url"
echo IconIndex=0 >> "%desktop%\音乐制作工作室.url"
echo IconFile="%SystemRoot%\System32\SHELL32.dll" >> "%desktop%\音乐制作工作室.url"

:: 创建工具快捷方式
if not exist "%desktop%\音乐工具" mkdir "%desktop%\音乐工具"

:: 参数生成器
echo [InternetShortcut] > "%desktop%\音乐工具\参数生成器.url"
echo URL="file:///%CD%\01_ParamGen\ParamGen.bat" >> "%desktop%\音乐工具\参数生成器.url"

:: MIDI生成器
echo [InternetShortcut] > "%desktop%\音乐工具\MIDI生成器.url"
echo URL="file:///%CD%\02_MIDIGen\MIDIGen.bat" >> "%desktop%\音乐工具\MIDI生成器.url"

:: 音频混合器
echo [InternetShortcut] > "%desktop%\音乐工具\音频混合器.url"
echo URL="file:///%CD%\03_AudioMix\AudioMix.bat" >> "%desktop%\音乐工具\音频混合器.url"

:: 人声处理器
echo [InternetShortcut] > "%desktop%\音乐工具\人声处理器.url"
echo URL="file:///%CD%\Tools\ProcessVocal.bat" >> "%desktop%\音乐工具\人声处理器.url"

:: 批量处理器
echo [InternetShortcut] > "%desktop%\音乐工具\批量处理器.url"
echo URL="file:///%CD%\Tools\BatchProcess.bat" >> "%desktop%\音乐工具\批量处理器.url"

echo 快捷方式创建完成！
echo 位置：桌面\音乐工具\
pause