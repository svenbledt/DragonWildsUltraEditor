@echo off
REM ============================================================
REM  DragonWilds: Ultra Editor - ONE-CLICK dist builder
REM
REM  Double-click this file and it runs the whole release
REM  pipeline end to end:
REM
REM    [1] Extract game data from the game paks (CUE4Parse
REM        --dump-data -> tools\game_dump\ItemDumper_*.jsonl)
REM    [2] Extract every item icon from the paks (-> data\icons)
REM    [3] Regenerate the editor data tables from the dumps
REM        (data\item_ids.py, pickup_ids.py, unlock_ids.py,
REM         shrine_ids.py, doctor_ids.py - doctor runs LAST)
REM    [4] Run the test suite (aborts the dist on any failure)
REM    [5] Compile the exe + zip via build_exe.bat
REM        -> dist\DragonWildsUltraEditor-standalone.zip
REM
REM  Requirements: the game installed (Steam), .NET 10 SDK
REM  ('dotnet'), Python launcher ('py'). Any step failing stops
REM  the pipeline - nothing half-built lands in dist\.
REM
REM  Before uploading to NexusMods: load an edited save in the
REM  actual game once. That is the release gate.
REM ============================================================
setlocal
cd /d "%~dp0"

echo(
echo ============================================================
echo  DragonWilds Ultra Editor - one-click dist pipeline
echo ============================================================

REM --- 0. Tooling checks ---------------------------------------
where dotnet >nul 2>nul
if errorlevel 1 ( echo [ERROR] 'dotnet' not found. Install the .NET 10 SDK. & goto :fail )
where py >nul 2>nul
if errorlevel 1 ( echo [ERROR] Python launcher 'py' not found. Install Python 3. & goto :fail )

REM --- 1. Extract game data from the paks ----------------------
echo(
echo [1/5] Extracting game data from the game files (--dump-data) ...
pushd tools\icon_extractor
dotnet run -c Release -- --dump-data
if errorlevel 1 ( popd & echo [ERROR] Game-data extraction failed. & goto :fail )
popd

REM --- 2. Extract item icons from the paks ---------------------
echo(
echo [2/5] Extracting item icons from the game files ...
pushd tools\icon_extractor
dotnet run -c Release
if errorlevel 1 ( popd & echo [ERROR] Icon extraction failed. & goto :fail )
popd

REM --- 3. Regenerate the editor data tables --------------------
REM  Order matters: doctor_ids reads the good sets, so it runs last.
echo(
echo [3/5] Regenerating editor data tables from the dumps ...
pushd tools\game_dump
for %%S in (build_item_ids.py build_pickup_ids.py build_recipe_ids.py build_building_ids.py build_mount_ids.py build_shrine_ids.py build_doctor_ids.py) do (
    echo   --- %%S ---
    py %%S
    if errorlevel 1 ( popd & echo [ERROR] %%S failed. & goto :fail )
)
popd

REM --- 4. Test suite -------------------------------------------
echo(
echo [4/5] Running the test suite ...
py -m pytest tests -q
if errorlevel 1 ( echo [ERROR] Tests failed - dist aborted. & goto :fail )

REM --- 5. Compile exe + zip ------------------------------------
echo(
echo [5/5] Building the exe and dist zip ...
call build_exe.bat
if errorlevel 1 ( echo [ERROR] Exe build failed. & goto :fail )

echo(
echo ============================================================
echo  DIST COMPLETE
echo    Upload : dist\DragonWildsUltraEditor-standalone.zip
echo(
echo  Release gate: load an edited save in the actual game
echo  before uploading to NexusMods.
echo ============================================================
endlocal
pause
exit /b 0

:fail
echo(
echo ------------------------------------------------------------
echo  DIST FAILED - see the messages above. Nothing was shipped.
echo ------------------------------------------------------------
endlocal
pause
exit /b 1
