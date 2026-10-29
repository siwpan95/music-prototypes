@echo off
chcp 65001 >nul
title 配置文件生成器
color 0F

echo 生成系统配置文件...
echo.

if not exist "Config\" mkdir "Config"

:system
echo 系统配置
echo.
set /p sample_rate=采样率 (默认44100): 
if not defined sample_rate set sample_rate=44100
set /p buffer_size=缓冲区大小 (默认2048): 
if not defined buffer_size set buffer_size=2048
set /p channels=声道数 (1-立体声 2-单声道, 默认2): 
if not defined channels set channels=2

:audio
echo.
echo 音频配置
echo.
if exist "Libs\SoundFonts\*.sf2" (
    dir "Libs\SoundFonts\*.sf2" /b
    echo.
    set /p soundfont=选择音色库: 
    if not defined soundfont (
        for %%f in ("Libs\SoundFonts\*.sf2") do (
            set soundfont=%%~nxf
            goto :got_soundfont
        )
    )
) else (
    set soundfont=default.sf2
)
:got_soundfont

set /p normalize_output=归一化输出? (Y/N, 默认Y): 
if /i "!normalize_output!"=="N" (
    set normalize=false
) else (
    set normalize=true
)

:midi
echo.
echo MIDI配置
echo.
set /p default_tempo=默认曲速 (BPM, 默认120): 
if not defined default_tempo set default_tempo=120
set /p time_signature=拍号 (默认4/4): 
if not defined time_signature set time_signature=4/4

:paths
echo.
echo 路径配置
echo.
set /p data_path=数据路径 (默认Data): 
if not defined data_path set data_path=Data
set /p output_path=输出路径 (默认Output): 
if not defined output_path set output_path=Output

:generate
echo.
echo 正在生成配置文件...
(
echo [System]
echo SampleRate=!sample_rate!
echo BufferSize=!buffer_size!
echo Channels=!channels!
echo.
echo [Audio]
echo SoundFont=!soundfont!
echo NormalizeOutput=!normalize!
echo.
echo [MIDI]
echo DefaultTempo=!default_tempo!
echo TimeSignature=!time_signature!
echo.
echo [Paths]
echo DataPath=!data_path!
echo OutputPath=!output_path!
echo InstrumentsPath=!data_path!\Instruments
echo MIDIPath=!data_path!\MIDI
echo AudioPath=!data_path!\Audio
echo ProjectsPath=!output_path!\Projects
echo RendersPath=!output_path!\Renders
echo ExportsPath=!output_path!\Exports
) > "Config\Studio.ini"

echo 配置文件已生成: Config\Studio.ini
echo.
echo 正在创建目录结构...
if not exist "!data_path!\Instruments" mkdir "!data_path!\Instruments"
if not exist "!data_path!\MIDI" mkdir "!data_path!\MIDI"
if not exist "!data_path!\Audio" mkdir "!data_path!\Audio"
if not exist "!output_path!\Projects" mkdir "!output_path!\Projects"
if not exist "!output_path!\Renders" mkdir "!output_path!\Renders"
if not exist "!output_path!\Exports" mkdir "!output_path!\Exports"

echo 目录结构创建完成
pause