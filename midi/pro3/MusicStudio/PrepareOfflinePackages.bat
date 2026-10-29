@echo off
chcp 65001 >nul
title 准备离线安装包
color 0E

echo 准备离线安装包...
echo 此脚本将下载所有必要的依赖包以便离线安装。
echo.

if not exist "OfflinePackages" mkdir "OfflinePackages"
cd OfflinePackages

:: 下载Python安装包
echo 下载Python 3.9.7...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe' -OutFile 'python-3.9.7-amd64.exe'"

:: 下载FFmpeg
echo 下载FFmpeg...
powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'"

:: 下载音色库
echo 下载音色库...
powershell -Command "Invoke-WebRequest -Uri 'https://downloads.sourceforge.net/project/fluid-soundfonts/FluidR3_GM/FluidR3_GM.sf2' -OutFile 'FluidR3_GM.sf2'"

:: 下载虚拟MIDI合成器
echo 下载虚拟MIDI合成器...
powershell -Command "Invoke-WebRequest -Uri 'https://coolsoft.altervista.org/download/virtualmidisynth/VirtualMIDISynthSetup.exe' -OutFile 'VirtualMIDISynthSetup.exe'"

:: 创建Python包缓存
if not exist "pip" mkdir "pip"
cd pip

echo 下载Python依赖包...
pip download numpy==1.21.0
pip download pygame==2.1.0
pip download pretty_midi==0.2.9
pip download soundfile==0.10.3
pip download scipy==1.7.0
pip download librosa==0.9.0
pip download pydub==0.25.1
pip download audioread==2.1.9

cd ..
cd ..

:: 创建安装说明
echo 创建安装说明...
(
echo 离线安装包说明
echo ==============
echo.
echo 包含组件：
echo 1. Python 3.9.7
echo 2. FFmpeg
echo 3. FluidR3_GM 音色库
echo 4. VirtualMIDISynth
echo 5. Python依赖包
echo.
echo 使用方法：
echo 1. 将整个OfflinePackages文件夹复制到目标计算机
echo 2. 运行Install.bat
echo 3. 系统将自动安装所有组件
echo.
echo 注意：需要管理员权限
) > OfflinePackages\README.txt

echo 离线安装包准备完成！
dir OfflinePackages
pause