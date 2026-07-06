@echo off
REM ============================================================
REM  DragonWilds: Ultra Editor - ONE-CLICK dist builder
REM
REM  Double-click and it runs the whole release pipeline:
REM    [1/5] Extract game data from the paks (--dump-data)
REM    [2/5] Extract every item icon from the paks
REM    [3/5] Regenerate the editor data tables (doctor LAST)
REM    [4/5] Run the test suite (red test = dist aborted)
REM    [5/5] Compile the exe + zip via build_exe.bat
REM
REM  Requirements: the game installed (Steam), .NET 10 SDK
REM  ('dotnet'), Python launcher ('py'). Any step failing stops
REM  the pipeline - nothing half-built lands in dist\.
REM
REM  Before uploading to NexusMods: load an edited save in the
REM  actual game once. That is the release gate.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
title DragonWilds Ultra Editor - dist pipeline

REM --- ANSI colors (Windows Terminal / Win11 default) ----------
for /f %%a in ('powershell -NoProfile -Command "[char]27"') do set "ESC=%%a"
set "R=%ESC%[0m"
set "B=%ESC%[97m"
set "CY=%ESC%[96m"
set "GN=%ESC%[92m"
set "RD=%ESC%[91m"
set "YL=%ESC%[93m"
set "DM=%ESC%[90m"

set "STEPS=5"
set "S1=Extract game data from the paks"
set "S2=Extract item icons from the paks"
set "S3=Regenerate editor data tables"
set "S4=Run the test suite"
set "S5=Compile exe + package dist zip"

echo(
echo %CY%============================================================%R%
echo %CY%      DragonWilds Ultra Editor  -  dist pipeline%R%
echo %CY%============================================================%R%
echo   %DM%[1/5]%R% %S1%
echo   %DM%[2/5]%R% %S2%
echo   %DM%[3/5]%R% %S3%
echo   %DM%[4/5]%R% %S4%
echo   %DM%[5/5]%R% %S5%
echo %CY%============================================================%R%

REM --- 0. Tooling checks ---------------------------------------
where dotnet >nul 2>nul
if errorlevel 1 ( echo %RD%[ERROR]%R% 'dotnet' not found. Install the .NET 10 SDK. & goto :fail )
where py >nul 2>nul
if errorlevel 1 ( echo %RD%[ERROR]%R% Python launcher 'py' not found. Install Python 3. & goto :fail )
REM  fail here, not 10 minutes in: a running editor locks dist\ files
REM  and step 5's clean + zip would die on them (/FO CSV because the
REM  default tasklist table truncates the long image name)
tasklist /FI "IMAGENAME eq DragonWildsUltraEditor.exe" /NH /FO CSV 2>nul | find /I "DragonWildsUltraEditor.exe" >nul
if not errorlevel 1 ( echo %RD%[ERROR]%R% DragonWildsUltraEditor.exe is running - close the editor first, it locks files in dist\. & goto :fail )

call :epoch
set "PIPE_START=!EPOCH!"

REM --- 1. Extract game data from the paks ----------------------
call :step_begin 1 "%S1%  (--dump-data -> tools\game_dump)"
pushd tools\icon_extractor
dotnet run -c Release -- --dump-data
if errorlevel 1 ( popd & goto :fail )
popd
call :step_end 1

REM --- 2. Extract item icons from the paks ---------------------
call :step_begin 2 "%S2%  (-> data\icons)"
pushd tools\icon_extractor
dotnet run -c Release
if errorlevel 1 ( popd & goto :fail )
popd
call :step_end 2

REM --- 3. Regenerate the editor data tables --------------------
REM  Order matters: doctor_ids reads the good sets, so it runs last.
call :step_begin 3 "%S3%  (doctor runs last)"
pushd tools\game_dump
for %%S in (build_item_ids.py build_pickup_ids.py build_recipe_ids.py build_building_ids.py build_mount_ids.py build_shrine_ids.py build_doctor_ids.py) do (
    echo(
    echo %YL%  --- %%S ---%R%
    py %%S
    if errorlevel 1 ( popd & echo %RD%[ERROR]%R% %%S failed. & goto :fail )
)
popd
call :step_end 3

REM --- 4. Test suite -------------------------------------------
call :step_begin 4 "%S4%"
py -m pytest tests -q
if errorlevel 1 ( echo %RD%[ERROR]%R% Tests failed - dist aborted. & goto :fail )
call :step_end 4

REM --- 5. Compile exe + zip ------------------------------------
call :step_begin 5 "%S5%  (build_exe.bat)"
call build_exe.bat
if errorlevel 1 ( goto :fail )
call :step_end 5

REM --- Summary -------------------------------------------------
call :epoch
set /a DUR=EPOCH-PIPE_START
set /a DMIN=DUR/60, DSEC=DUR%%60
echo(
echo %GN%============================================================%R%
echo %GN%  DIST COMPLETE%R%   %DM%total !DMIN!m !DSEC!s%R%
echo %GN%============================================================%R%
for /l %%i in (1,1,%STEPS%) do (
    set "NM=!S%%i!                                              "
    echo   %GN%[%%i/%STEPS%] OK%R%  !NM:~0,38! %DM%!DUR_%%i!%R%
)
echo(
echo   Upload : %B%dist\DragonWildsUltraEditor-standalone.zip%R%
echo(
echo   %YL%Release gate:%R% load an edited save in the actual game
echo   before uploading to NexusMods.
echo %GN%============================================================%R%
endlocal
pause
exit /b 0

REM --- helpers -------------------------------------------------
:epoch
for /f %%t in ('powershell -NoProfile -Command "[DateTimeOffset]::Now.ToUnixTimeSeconds()"') do set "EPOCH=%%t"
exit /b

:step_begin
set "CUR_STEP=%~1"
set "CUR_NAME=%~2"
call :epoch
set "T_START=!EPOCH!"
echo(
echo %CY%------------------------------------------------------------%R%
REM  delayed expansion here: the title may contain > or ( which cmd
REM  would otherwise re-parse as redirection
echo %CY%  [STEP %~1/%STEPS%]%R%  %B%!CUR_NAME!%R%   %DM%started %TIME:~0,8%%R%
echo %CY%------------------------------------------------------------%R%
exit /b

:step_end
call :epoch
set /a DUR=EPOCH-T_START
set /a DMIN=DUR/60, DSEC=DUR%%60
if !DMIN! equ 0 ( set "DSTR=!DSEC!s" ) else if !DSEC! lss 10 ( set "DSTR=!DMIN!m 0!DSEC!s" ) else ( set "DSTR=!DMIN!m !DSEC!s" )
set "DUR_%~1=!DSTR!"
echo %GN%  [STEP %~1/%STEPS%] OK%R%  %DM%(!DSTR!)%R%
exit /b

:fail
echo(
echo %RD%============================================================%R%
echo %RD%  DIST FAILED at step !CUR_STEP!/%STEPS% - see messages above.%R%
echo %RD%  Nothing was shipped to dist\.%R%
echo %RD%============================================================%R%
endlocal
pause
exit /b 1
