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
REM  tools\ is dev-only and is NOT bundled (main.py never
REM  imports it).
REM
REM  This script ONLY compiles + zips. For the full release
REM  pipeline (extract game data + icons from the paks,
REM  regenerate the data tables, run tests, then build),
REM  double-click make_dist.bat instead.
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
REM Compile OUTSIDE the project tree: cloud-sync clients (Google Drive etc.)
REM watching this folder race Nuitka's scratch files mid-build and crash it
REM (observed twice: main.dist and module.PIL.c vanished during compilation).
REM Only the finished app folder and zip are placed into dist\ at the end.
set "BUILDDIR=%LOCALAPPDATA%\DragonWildsUltraEditor-build"

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
REM  Nuitka's tk-inter plugin needs Tcl/Tk's script library on disk.
REM  Python 3.14+ from the Python install manager ships Tcl 9 with that
REM  library packed inside the DLL (//zipfs:), which Nuitka cannot
REM  bundle ("FATAL: tk-inter: Could not find Tcl"). So pick the newest
REM  installed Python whose Tcl library is a real folder, and rebuild
REM  the venv if it was created from an unusable one. A candidate only
REM  counts when it prints its own interpreter path: the install
REM  manager's "py -3.13" exits 0 even when 3.13 is not installed.
set "TCLCHECK_PY=%TEMP%\dwue_tclcheck.py"
> "%TCLCHECK_PY%" echo import os, sys, tkinter
>>"%TCLCHECK_PY%" echo if os.path.isdir(tkinter.Tcl().eval("info library")): print(sys.executable)
set "PYEXE="
for %%V in (3.13 3.12 3.11 3.10 3) do (
    if not defined PYEXE (
        for /f "usebackq delims=" %%P in (`py -%%V "%TCLCHECK_PY%" 2^>nul`) do (
            if exist "%%P" set "PYEXE=%%P"
        )
    )
)
if not defined PYEXE (
    del /q "%TCLCHECK_PY%" 2>nul
    echo [ERROR] No installed Python has a Tcl/Tk library Nuitka can bundle.
    echo         Install Python 3.13 or 3.12 from https://www.python.org/downloads/
    echo         with the "tcl/tk and IDLE" option ticked, then run this again.
    goto :fail
)
if exist "%VPY%" (
    set "VENV_OK="
    for /f "usebackq delims=" %%P in (`call "%VPY%" "%TCLCHECK_PY%" 2^>nul`) do set "VENV_OK=1"
    if not defined VENV_OK (
        echo [1/6] Existing "%VENV%" uses a Python without a usable Tcl/Tk - rebuilding it.
        rmdir /s /q "%VENV%"
        if exist "%VENV%" ( echo [ERROR] Could not remove "%VENV%" - close anything using it. & goto :fail )
    )
)
del /q "%TCLCHECK_PY%" 2>nul
if not exist "%VPY%" (
    echo [1/6] Creating build virtual environment "%VENV%" from !PYEXE! ...
    "!PYEXE!" -m venv "%VENV%"
    if errorlevel 1 ( echo [ERROR] Could not create the virtual environment. & goto :fail )
) else (
    echo [1/6] Reusing existing build venv "%VENV%".
)

REM --- 3. Install dependencies + Nuitka -----------------------
REM  --no-compile: the venv lives in the project tree, and a cloud-sync
REM  client racing pip's freshly written .pyc files makes the install
REM  abort with "assert os.path.exists(pyc_path)".
echo [2/6] Upgrading pip ...
"%VPY%" -m pip install --no-compile --upgrade pip
if errorlevel 1 ( echo [ERROR] pip upgrade failed. & goto :fail )

echo [3/6] Installing project requirements + Nuitka ...
"%VPY%" -m pip install --no-compile -r requirements.txt
if errorlevel 1 ( echo [ERROR] Installing requirements.txt failed. & goto :fail )
"%VPY%" -m pip install --no-compile --upgrade nuitka
if errorlevel 1 ( echo [ERROR] Installing Nuitka failed. & goto :fail )

REM  --venv-only: stop here with a ready .venv-build (make_dist.bat uses
REM  it to run the test suite before compiling).
if /I "%~1"=="--venv-only" (
    echo [venv] "%VENV%" is ready.
    endlocal
    exit /b 0
)

REM --- 4. Clean previous build output -------------------------
REM  A running editor locks its exe and (on older builds) icon pngs
REM  inside dist\, which makes the rmdir below fail half-way and the
REM  final Compress-Archive die on a locked file. /FO CSV: the default
REM  table truncates long image names, so find would never match.
tasklist /FI "IMAGENAME eq %APPNAME%.exe" /NH /FO CSV 2>nul | "%SystemRoot%\System32\find.exe" /I "%APPNAME%.exe" >nul
if not errorlevel 1 (
    echo [ERROR] %APPNAME%.exe is running. Close the editor first -
    echo         it locks files in dist\, so cleaning/zipping fails.
    goto :fail
)
echo [4/6] Cleaning previous build artifacts ...
if exist "%BUILDDIR%" rmdir /s /q "%BUILDDIR%"
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
    --file-version=13.1.0.0 ^
    --product-version=13.1.0.0 ^
    --assume-yes-for-downloads ^
    --msvc=latest ^
    --output-dir="%BUILDDIR%" ^
    --output-filename=%APPNAME%.exe ^
    main.py
if errorlevel 1 ( echo [ERROR] Nuitka build failed. See the log above. & goto :fail )

if not exist "%BUILDDIR%\main.dist\%APPNAME%.exe" (
    echo [ERROR] Build reported success but the exe is missing.
    goto :fail
)

REM --- 6. Package the folder into a distributable zip ---------
REM  Rename + zip + verify entirely inside %BUILDDIR%: cloud-sync
REM  clients (Google Drive) start hashing files the moment they land
REM  in the project tree, and Compress-Archive then dies on their
REM  locks. Only two moves touch dist\ at the end.
REM  Compress-Archive failures are non-terminating (powershell.exe
REM  still exits 0 and a truncated zip gets reported as BUILD
REM  COMPLETE), so it runs with -ErrorAction Stop in a try/catch and
REM  the zip's file count is checked against the folder afterwards.
echo [6/6] Packaging dist\%APPNAME%-standalone.zip ...
if not exist "dist" mkdir "dist"
ren "%BUILDDIR%\main.dist" "%APPNAME%"
if errorlevel 1 ( echo [ERROR] Could not rename the build folder. & goto :fail )
powershell -NoProfile -Command "try { Compress-Archive -Path '%BUILDDIR%\%APPNAME%' -DestinationPath '%BUILDDIR%\%APPNAME%-standalone.zip' -CompressionLevel Optimal -Force -ErrorAction Stop } catch { Write-Error $_; exit 1 }; Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip = [IO.Compression.ZipFile]::OpenRead('%BUILDDIR%\%APPNAME%-standalone.zip'); $n = @($zip.Entries | Where-Object { $_.Name }).Count; $zip.Dispose(); $files = @(Get-ChildItem -LiteralPath '%BUILDDIR%\%APPNAME%' -Recurse -File).Count; if ($n -ne $files) { Write-Error ('zip holds {0} files but the folder has {1}' -f $n, $files); exit 1 }"
if errorlevel 1 ( echo [ERROR] Zipping the standalone folder failed - nothing was placed in dist. & goto :fail )
move "%BUILDDIR%\%APPNAME%-standalone.zip" "dist\%APPNAME%-standalone.zip" >nul
if errorlevel 1 ( echo [ERROR] Could not move the zip into dist. & goto :fail )
REM  cmd's `move` cannot move a DIRECTORY across volumes (build dir is
REM  on %LOCALAPPDATA%'s drive, the project may live on another) - it
REM  fails with "Access denied". robocopy /MOVE handles both cases;
REM  exit codes 0-7 mean success, 8+ mean failure.
robocopy "%BUILDDIR%\%APPNAME%" "dist\%APPNAME%" /E /MOVE /NFL /NDL /NJH /NJS >nul
if errorlevel 8 ( echo [ERROR] Could not move the app folder into dist. & goto :fail )
if exist "%BUILDDIR%" rmdir /s /q "%BUILDDIR%"

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
call :pause_if_clicked
endlocal
exit /b 0

:fail
echo(
echo ------------------------------------------------------------
echo  BUILD FAILED - nothing was produced. See messages above.
echo ------------------------------------------------------------
call :pause_if_clicked
endlocal
exit /b 1

REM  Keep the window open when this file was double-clicked (Explorer
REM  starts it as cmd /c "...build_exe.bat"); stay silent when it runs
REM  from a terminal or is CALLed by make_dist.bat, which pauses itself.
:pause_if_clicked
echo !cmdcmdline! | "%SystemRoot%\System32\find.exe" /I "%~nx0" >nul
if not errorlevel 1 pause
exit /b
