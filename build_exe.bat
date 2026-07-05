@echo off
REM ============================================================
REM  DragonWilds: Ultra Editor - single-file EXE builder
REM
REM  Builds dist\DragonWildsUltraEditor.exe from launcher.py.
REM  Uses an isolated build venv (.venv-build) so it never
REM  touches your global Python. Bundles the sv-ttk (Sun Valley)
REM  theme via --collect-data. ue4ss_dumper\ is dev-only and is
REM  NOT bundled (launcher.py never imports it).
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
echo  Building %APPNAME%.exe
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
    echo [1/5] Creating build virtual environment "%VENV%" ...
    py -m venv "%VENV%"
    if errorlevel 1 ( echo [ERROR] Could not create the virtual environment. & goto :fail )
) else (
    echo [1/5] Reusing existing build venv "%VENV%".
)

REM --- 3. Install dependencies + PyInstaller ------------------
echo [2/5] Upgrading pip ...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 ( echo [ERROR] pip upgrade failed. & goto :fail )

echo [3/5] Installing project requirements + PyInstaller ...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] Installing requirements.txt failed. & goto :fail )
"%VPY%" -m pip install pyinstaller
if errorlevel 1 ( echo [ERROR] Installing PyInstaller failed. & goto :fail )

REM --- 4. Clean previous build output -------------------------
echo [4/5] Cleaning previous build artifacts ...
if exist "build" rmdir /s /q "build"
if exist "dist\%APPNAME%.exe" del /q "dist\%APPNAME%.exe"
if exist "%APPNAME%.spec" del /q "%APPNAME%.spec"

REM --- 5. Build the single-file, windowed exe -----------------
echo [5/5] Running PyInstaller (this can take a minute) ...
"%VPY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APPNAME%" ^
    --icon "Dragonwilds_Editor.ico" ^
    --add-data "Dragonwilds_Editor.ico;." ^
    --add-data "Dragonwilds_Editor.png;." ^
    --collect-data sv_ttk ^
    launcher.py
if errorlevel 1 ( echo [ERROR] PyInstaller build failed. See the log above. & goto :fail )

if not exist "dist\%APPNAME%.exe" (
    echo [ERROR] Build reported success but dist\%APPNAME%.exe is missing.
    goto :fail
)

echo(
echo ============================================================
echo  BUILD COMPLETE
echo    dist\%APPNAME%.exe
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
