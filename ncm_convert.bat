@echo off
REM ---------------------------------------------------------------------------
REM  Encrypted music converter (local only, no network required)
REM  Usage A: drag & drop files/folders onto this .bat
REM  Usage B: ncm_convert.bat <path1> [<path2> ...] [-o out_dir] [-f fmt] [-b br]
REM  Input : ncm / qmc family (qmc0,qmc3,qmcflac,mflac,mgg,...) / tm cache /
REM          kgm / kgma / vpr / kwm / xm / mg3d / common audio files
REM  Output: -f mp3 (default) / flac / wav / aac / ogg / m4a / orig (decrypt only)
REM  Deps  : ncm_batch.py in same folder + ffmpeg in PATH (not needed for -f orig)
REM  After conversion the output folder opens automatically.
REM ---------------------------------------------------------------------------
setlocal enabledelayedexpansion
set "PY=python"
set "SCRIPT=%~dp0ncm_batch.py"

if "%~1"=="" (
    echo Please drag .ncm/.qmc/.kgm/.kwm/.xm files or folders onto this file,
    echo or run with arguments. Example: ncm_convert.bat D://Music -f flac
    pause
    exit /b 1
)

REM quote every argument to survive spaces in paths; remember first arg folder
set "ARGS="
set "FIRST="
for %%A in (%*) do (
    if not defined FIRST set "FIRST=%%~dpA"
    set "ARGS=!ARGS! "%%~A""
)

REM parse -o/--output value as the output dir (to open it afterwards)
set "OUTDIR="
call :parse_outdir %*
goto :after_parse

:parse_outdir
if "%~1"=="" goto :eof
if /i "%~1"=="-o" ( set "OUTDIR=%~2" & goto :eof )
if /i "%~1"=="--output" ( set "OUTDIR=%~2" & goto :eof )
shift
goto :parse_outdir

:after_parse

echo Input: %*
"%PY%" "%SCRIPT%" !ARGS!
set "RC=%errorlevel%"

REM open output folder on success
if %RC%==0 (
    if defined OUTDIR ( set "OPENDIR=%OUTDIR%" ) else ( set "OPENDIR=%FIRST%" )
    if defined OPENDIR (
        if exist "%OPENDIR%" (
            echo Opening output folder: %OPENDIR%
            start "" "%OPENDIR%"
        )
    )
)
echo.
echo All done.
pause
