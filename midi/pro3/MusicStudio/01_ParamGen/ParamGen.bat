@echo off
chcp 65001 >nul
title 参数生成器
color 0B

:main
cls
echo ========================================
echo       参数生成器
echo ========================================
echo.
echo 功能：
echo   1. 创建新乐器配置
echo   2. 从模板生成
echo   3. 编辑现有配置
echo   4. 批量生成
echo   5. 导入MIDI
echo   6. 返回主菜单
echo.
choice /C 123456 /N /M "请选择: "
if errorlevel 6 goto end
if errorlevel 5 goto import
if errorlevel 4 goto batch
if errorlevel 3 goto edit
if errorlevel 2 goto template
if errorlevel 1 goto create

:create
cls
echo 创建新乐器配置
echo.
set /p instr_name=乐器名称: 
set /p instr_type=乐器类型 (1.旋律 2.打击乐 3.和声): 
set /p midi_program=MIDI音色号 (0-127, 默认0): 
if not defined midi_program set midi_program=0
set /p volume=音量 (0-127, 默认100): 
if not defined volume set volume=100
set /p pan=声相 (0-127, 64=居中): 
if not defined pan set pan=64

echo 正在生成配置...
powershell -ExecutionPolicy Bypass -File "ParamGen.ps1" -Action Create -Name "%instr_name%" -Type %instr_type% -Program %midi_program% -Volume %volume% -Pan %pan%

if exist "Data\Instruments\%instr_name%.json" (
    echo 配置已保存: Data\Instruments\%instr_name%.json
) else (
    echo 生成失败
)
pause
goto main

:template
cls
echo 从模板生成
echo.
dir "01_ParamGen\Templates\*.json" /b
echo.
set /p template=选择模板文件名: 
if not exist "01_ParamGen\Templates\%template%" (
    echo 模板不存在
    pause
    goto main
)

set /p instr_name=新乐器名称: 
copy "01_ParamGen\Templates\%template%" "Data\Instruments\%instr_name%.json"
echo 已从模板创建: %instr_name%.json
pause
goto main

:edit
cls
echo 编辑现有配置
echo.
if not exist "Data\Instruments\*.json" (
    echo 没有找到配置文件
    pause
    goto main
)

dir "Data\Instruments\*.json" /b
echo.
set /p config=选择要编辑的文件: 
if not exist "Data\Instruments\%config%" (
    echo 文件不存在
    pause
    goto main
)

powershell -ExecutionPolicy Bypass -File "ParamGen.ps1" -Action Edit -File "Data\Instruments\%config%"
pause
goto main

:batch
cls
echo 批量生成配置
echo.
set /p count=生成数量: 
set /p prefix=文件名前缀: 
set /p pattern=模式类型 (1.音阶 2.琶音 3.随机): 

echo 正在批量生成...
for /l %%i in (1,1,%count%) do (
    set idx=00%%i
    set idx=!idx:~-3!
    powershell -ExecutionPolicy Bypass -File "ParamGen.ps1" -Action Batch -Index %%i -Prefix "%prefix%" -Pattern %pattern%
)
echo 批量生成完成
pause
goto main

:import
cls
echo 从MIDI导入配置
echo.
if not exist "Data\MIDI\*.mid" if not exist "Data\MIDI\*.midi" (
    echo MIDI目录为空
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

set /p out_name=输出配置名称: 
powershell -ExecutionPolicy Bypass -File "ParamGen.ps1" -Action Import -Midi "Data\MIDI\%midi_file%" -OutName "%out_name%"
echo 导入完成
pause
goto main

:end
exit