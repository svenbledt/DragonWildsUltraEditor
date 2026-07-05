@echo off
REM ============================================================================
REM  After pressing F8 in-game to produce the dump, run this to copy the dump
REM  into the project and regenerate item_ids.py.
REM ============================================================================

REM The mod writes to the game's working directory, which is Binaries\Win64.
set "GAMEDIR=F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64"

if exist "%GAMEDIR%\ItemDumper_items.jsonl" (
    copy /Y "%GAMEDIR%\ItemDumper_items.jsonl"       "%~dp0ItemDumper_items.jsonl" >nul
    if exist "%GAMEDIR%\ItemDumper_recipes.jsonl"    copy /Y "%GAMEDIR%\ItemDumper_recipes.jsonl"    "%~dp0ItemDumper_recipes.jsonl" >nul
    if exist "%GAMEDIR%\ItemDumper_mounts.jsonl"     copy /Y "%GAMEDIR%\ItemDumper_mounts.jsonl"     "%~dp0ItemDumper_mounts.jsonl" >nul
    if exist "%GAMEDIR%\ItemDumper_buildings.jsonl"  copy /Y "%GAMEDIR%\ItemDumper_buildings.jsonl"  "%~dp0ItemDumper_buildings.jsonl" >nul
    if exist "%GAMEDIR%\ItemDumper_diagnostics.txt"  copy /Y "%GAMEDIR%\ItemDumper_diagnostics.txt"  "%~dp0ItemDumper_diagnostics.txt" >nul
    echo Copied dump from the game folder.
) else (
    echo [WARN] No dump found in %GAMEDIR%.
    echo        Load a world and press F8 first, or the mod wrote elsewhere.
)

echo.
echo === Analyzing ITEM dump (dry run) ===
py "%~dp0build_item_ids.py" --dry-run
echo.
echo === Analyzing RECIPE dump (dry run) ===
py "%~dp0build_recipe_ids.py" --dry-run
echo.
echo === Analyzing MOUNT dump (dry run) ===
py "%~dp0build_mount_ids.py" --dry-run
echo.
echo === Analyzing BUILDING dump (dry run) ===
py "%~dp0build_building_ids.py" --dry-run
echo.
echo Review the reports above. To actually regenerate, run:
echo     py "%~dp0build_item_ids.py"       (rebuilds item_ids.py)
echo     py "%~dp0build_recipe_ids.py"      (rebuilds EMBEDDED_RECIPE_IDS in tab_extra.py)
echo     py "%~dp0build_mount_ids.py"       (rebuilds EMBEDDED_MOUNT_TAGS in tab_extra.py)
echo     py "%~dp0build_building_ids.py"    (rebuilds EMBEDDED_BUILDING_IDS in tab_extra.py)
echo (add --force only if you have verified the report looks right)
pause
