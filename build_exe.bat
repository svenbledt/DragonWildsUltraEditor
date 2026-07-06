@echo off
REM ============================================================
REM  DragonWilds: Ultra Editor - native EXE builder (Nuitka)
REM
REM  Compiles main.py to a native machine-code .exe with
REM  Nuitka (Python -> C -> real binary). This is used instead
REM  of PyInstaller to:
REM    * avoid the antivirus false-positives that got the old
REM      PyInstaller --onefile build flagged/deleted on Nexus,
REM    * ship a compiled binary with no extractable .pyc source.
REM
REM  Uses an isolated build venv (.venv-build) so it never
REM  touches your global Python. Bundles CustomTkinter, the
REM  data\icons item-icon set, and the app icon/about image.
REM  tools\ue4ss_dumper\ is dev-only and is NOT bundled (main.py never
REM  imports it).
REM
REM  Requires a C compiler. This build was verified with MSVC
REM  (Visual Studio 2022 Build Tools). If MSVC is missing,
REM  Nuitka will offer to download MinGW-w64 automatically.
REM
REM  Just double-click this file, or run it from a terminal.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "APPNAME=DragonWildsUltraEditor"
set "VENV=.venv-build"
set "VPY=%VENV%\Scripts\python.exe"

echo(
echo ============================================================
echo  Building %APPNAME%.exe  (Nuitka native compile)
echo ============================================================

REM --- 1. Require the Python launcher -------------------------
where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher 'py' was not found on PATH.
    echo         Install Python 3 from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH".
    goto :fail
)

REM --- 2. Create the isolated build venv ----------------------
if not exist "%VPY%" (
    echo [1/6] Creating build virtual environment "%VENV%" ...
    py -m venv "%VENV%"
    if errorlevel 1 ( echo [ERROR] Could not create the virtual environment. & goto :fail )
) else (
    echo [1/6] Reusing existing build venv "%VENV%".
)

REM --- 3. Install dependencies + Nuitka -----------------------
echo [2/6] Upgrading pip ...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 ( echo [ERROR] pip upgrade failed. & goto :fail )

echo [3/6] Installing project requirements + Nuitka ...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] Installing requirements.txt failed. & goto :fail )
"%VPY%" -m pip install --upgrade nuitka
if errorlevel 1 ( echo [ERROR] Installing Nuitka failed. & goto :fail )

REM --- 4. Clean previous build output -------------------------
echo [4/6] Cleaning previous build artifacts ...
if exist "dist\main.build" rmdir /s /q "dist\main.build"
if exist "dist\main.dist" rmdir /s /q "dist\main.dist"
if exist "dist\%APPNAME%" rmdir /s /q "dist\%APPNAME%"
if exist "dist\%APPNAME%-standalone.zip" del /q "dist\%APPNAME%-standalone.zip"

REM --- 5. Compile a standalone (folder) windowed exe ----------
REM  --standalone       : app + its DLLs in a folder, NO onefile
REM       self-extracting stub. The stub is what CrowdStrike /
REM       Symantec / Elastic ML heuristics flag as "dropper-like",
REM       so the folder form is the least likely to be quarantined.
REM  --enable-plugin=tk-inter : bundle Tcl/Tk so tkinter/CustomTkinter works when frozen
REM  --include-package-data=customtkinter : bundle CustomTkinter's theme/asset files
REM  --include-package=ui/core/data : ui/app.py loads pages with
REM       importlib.import_module() from a string table, which Nuitka's
REM       static analysis cannot follow. Without these the frozen exe is
REM       missing every page module (and the core/data modules only they
REM       import) and each page falls back to the "Coming soon..."
REM       placeholder.
REM  --include-data-dir=data/icons=data/icons : bundle the 754-icon item-icon set
REM  --windows-console-mode=disable : no console window (GUI app)
REM  version/company metadata : unsigned binaries with real metadata look
REM       far less suspicious to AV heuristics than blank ones
echo [5/6] Compiling with Nuitka (first run can take several minutes) ...
"%VPY%" -m nuitka ^
    --standalone ^
    --enable-plugin=tk-inter ^
    --include-package-data=customtkinter ^
    --include-package=ui ^
    --include-package=core ^
    --include-package=data ^
    --include-data-dir=data/icons=data/icons ^
    --include-data-files=Dragonwilds_Editor.ico=Dragonwilds_Editor.ico ^
    --include-data-files=Dragonwilds_Editor.png=Dragonwilds_Editor.png ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=Dragonwilds_Editor.ico ^
    --company-name="DragonWilds Ultra Editor" ^
    --product-name="DragonWilds Ultra Editor" ^
    --file-description="DragonWilds Ultra Save Editor" ^
    --file-version=13.0.0.0 ^
    --product-version=13.0.0.0 ^
    --assume-yes-for-downloads ^
    --msvc=latest ^
    --output-dir=dist ^
    --output-filename=%APPNAME%.exe ^
    main.py
if errorlevel 1 ( echo [ERROR] Nuitka build failed. See the log above. & goto :fail )

if not exist "dist\main.dist\%APPNAME%.exe" (
    echo [ERROR] Build reported success but the exe is missing.
    goto :fail
)

REM --- 6. Package the folder into a distributable zip ---------
echo [6/6] Packaging dist\%APPNAME%-standalone.zip ...
rename "dist\main.dist" "%APPNAME%"
if errorlevel 1 ( echo [ERROR] Could not rename the build folder. & goto :fail )
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%APPNAME%' -DestinationPath 'dist\%APPNAME%-standalone.zip' -CompressionLevel Optimal"
if errorlevel 1 ( echo [ERROR] Zipping the standalone folder failed. & goto :fail )
if exist "dist\main.build" rmdir /s /q "dist\main.build"

echo(
echo ============================================================
echo  BUILD COMPLETE
echo    Folder : dist\%APPNAME%\%APPNAME%.exe
echo    Upload : dist\%APPNAME%-standalone.zip
echo(
echo  This is the standalone (folder) form - no onefile stub -
echo  which is the least likely to be quarantined by NexusMods'
echo  scanner. Upload the .zip to Nexus.
echo(
echo  Tip: the app writes settings.json next to wherever the
echo  exe is launched from. Run it on a COPY of a save first.
echo ============================================================
endlocal
exit /b 0

:fail
echo(
echo ------------------------------------------------------------
echo  BUILD FAILED - nothing was produced. See messages above.
echo ------------------------------------------------------------
endlocal
exit /b 1
