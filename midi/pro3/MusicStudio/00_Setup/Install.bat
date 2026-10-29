@echo off
chcp 65001 >nul
title 音乐制作系统 - 安装程序
color 0A

echo ========================================
echo   音乐制作系统 v2.0 - 轻量级版
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 需要管理员权限以安装必要的组件
    echo 请以管理员身份运行此脚本
    pause
    exit /b 1
)

:: 设置路径
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
:: 2026-09-23 去本地化：本脚本所有路径都按自身位置推导，不再依赖当前工作目录。
::   SCRIPT_DIR = 本 bat 所在目录（00_Setup\）；MUSICSTUDIO_ROOT = 其上级（MusicStudio 根）。
::   原先 cd /d %SCRIPT_DIR% 之后仍用 .\00_Setup\...，会叠加成 00_Setup\00_Setup\...，本次一并修正。

:: 检查Python
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 未检测到Python，正在安装Python 3.9...
    powershell -Command "Start-Process -Wait -FilePath '%SCRIPT_DIR%OfflinePackages\python-3.9.7-amd64.exe' -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1'"
    echo Python安装完成
) else (
    echo Python已安装
)

:: 检查FFmpeg
:: 去本地化（2026-09-23）：解包目录不再写死 C 盘固定路径。
::   解包目录 FFMPEG_HOME 优先级：环境变量 FFMPEG_HOME > 本 bat 所在目录（%~dp0 = 00_Setup\）
::   的上级即 MusicStudio 根目录下的 Libs\ffmpeg。追加到 PATH 的目录恒为 %FFMPEG_HOME%\bin，
::   与解包目录同源，故路径逻辑自洽；离线包路径同样按 %~dp0 推导，不依赖当前工作目录。
echo [2/6] 检查FFmpeg...
:: MUSICSTUDIO_ROOT 必须**无条件**先算出来（否则用户预设了 FFMPEG_HOME 时，下面用到的 %MUSICSTUDIO_ROOT% 会是空值）
for %%I in ("%~dp0..") do set "MUSICSTUDIO_ROOT=%%~fI"
if not defined FFMPEG_HOME set "FFMPEG_HOME=%MUSICSTUDIO_ROOT%\Libs\ffmpeg"
where ffmpeg >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在安装FFmpeg 到 %FFMPEG_HOME% ...
    powershell -Command "Expand-Archive -Path '%SCRIPT_DIR%OfflinePackages\ffmpeg.zip' -DestinationPath '%FFMPEG_HOME%' -Force"
    setx PATH "%PATH%;%FFMPEG_HOME%\bin" /M
    echo FFmpeg安装完成，解包目录：%FFMPEG_HOME%
    echo 已将 %FFMPEG_HOME%\bin 追加到系统 PATH（需新开终端生效）
) else (
    echo FFmpeg已安装
)

:: 检查MIDI驱动程序
echo [3/6] 检查MIDI支持...
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\MCI" /v "Sequencer" >nul 2>&1
if %errorLevel% neq 0 (
    echo 配置MIDI支持...
    powershell -Command "Start-Process -Wait -FilePath '%SCRIPT_DIR%OfflinePackages\VirtualMIDISynthSetup.exe' -ArgumentList '/S'"
    echo MIDI驱动程序安装完成
) else (
    echo MIDI支持已就绪
)

:: 安装Python依赖
echo [4/6] 安装Python依赖库...
if exist "%MUSICSTUDIO_ROOT%\requirements.txt" (
    echo 正在安装依赖包（这可能需要几分钟）...
    python -m pip install --upgrade pip
    pip install -r "%MUSICSTUDIO_ROOT%\requirements.txt" --no-index --find-links="%SCRIPT_DIR%OfflinePackages\pip"
    echo 依赖安装完成
) else (
    echo 正在安装核心依赖...
    for %%p in (numpy,pygame,pretty_midi,soundfile) do (
        echo 安装 %%p...
        pip install "%SCRIPT_DIR%OfflinePackages\pip\%%p*.whl"
    )
)

:: 下载音色库
echo [5/6] 设置音色库...
if not exist "%MUSICSTUDIO_ROOT%\Libs\SoundFonts" mkdir "%MUSICSTUDIO_ROOT%\Libs\SoundFonts"
if not exist "%MUSICSTUDIO_ROOT%\Libs\SoundFonts\default.sf2" (
    echo 正在下载免费音色库...
    powershell -Command "Invoke-WebRequest -Uri 'https://downloads.sourceforge.net/project/fluid-soundfonts/FluidR3_GM/FluidR3_GM.sf2' -OutFile '%MUSICSTUDIO_ROOT%\Libs\SoundFonts\default.sf2'"
    echo 音色库下载完成
)

:: 创建示例项目
echo [6/6] 创建示例文件...
if not exist "%MUSICSTUDIO_ROOT%\Data\Instruments" mkdir "%MUSICSTUDIO_ROOT%\Data\Instruments"
if not exist "%MUSICSTUDIO_ROOT%\Data\MIDI" mkdir "%MUSICSTUDIO_ROOT%\Data\MIDI"
if not exist "%MUSICSTUDIO_ROOT%\Data\Audio" mkdir "%MUSICSTUDIO_ROOT%\Data\Audio"
if not exist "%MUSICSTUDIO_ROOT%\Output\Projects" mkdir "%MUSICSTUDIO_ROOT%\Output\Projects"
if not exist "%MUSICSTUDIO_ROOT%\Output\Renders" mkdir "%MUSICSTUDIO_ROOT%\Output\Renders"

:: 创建示例配置
if not exist "%MUSICSTUDIO_ROOT%\Config\Defaults.ini" (
    echo [System] > "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo SampleRate=44100 >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo Channels=2 >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo BufferSize=2048 >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo. >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo [Audio] >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo SoundFont=default.sf2 >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
    echo NormalizeOutput=true >> "%MUSICSTUDIO_ROOT%\Config\Defaults.ini"
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 已安装的组件：
echo   - Python 3.9+
echo   - FFmpeg
echo   - MIDI驱动程序
echo   - 音色库
echo   - Python音频库
echo.
echo 使用方法：
echo   1. 运行 MusicStudio.bat 启动主界面
echo   2. 或运行子模块的 .bat 文件
echo.
pause