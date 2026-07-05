@echo off
REM ============================================================================
REM  Re-create the directory junction that exposes our ItemDumper UE4SS mod
REM  inside the game's Mods folder. Run this once after a game update / reinstall
REM  (updates can wipe the Mods folder). Uses a junction because the project
REM  (C:) and the game (F:) live on different drives, so a true hardlink is not
REM  possible; a junction is the correct cross-volume equivalent.
REM ============================================================================

set "MODS=F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mods"
set "SRC=%~dp0ItemDumper"

if not exist "%MODS%" (
    echo [ERROR] UE4SS Mods folder not found:
    echo         %MODS%
    echo Edit MODS in this script if the game moved.
    pause
    exit /b 1
)

if exist "%MODS%\ItemDumper" (
    echo Removing existing link/folder...
    rmdir "%MODS%\ItemDumper" 2>nul
)

mklink /J "%MODS%\ItemDumper" "%SRC%"
if errorlevel 1 (
    echo [ERROR] Failed to create junction.
    pause
    exit /b 1
)

echo.
echo [OK] Junction created:
echo      %MODS%\ItemDumper  ^-^>  %SRC%
echo.
echo Now fully restart the game, load into a world, and press F8 to dump items.
pause
