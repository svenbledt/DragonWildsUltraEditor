# Building the DragonWilds Ultra Editor exe

## 1. Install dependencies

```
py -m pip install -r requirements.txt
py -m pip install pyinstaller
```

`sv-ttk` ships a Tcl theme that must be collected into the exe.

## 2. Build a single-file, windowed exe

```
py -m PyInstaller --noconfirm --onefile --windowed --collect-data sv_ttk launcher.py
```

- `--collect-data sv_ttk` bundles the Sun Valley `.tcl` theme assets. Without it
  the frozen app raises a Tcl error on startup; `theme.apply_theme` then falls
  back to the plain `clam` theme (usable but not the intended look).
- `--windowed` suppresses the console window.
- The `ue4ss_dumper/` directory is dev-only and is NOT imported by `launcher.py`,
  so it is never bundled.

The exe is written to `dist/launcher.exe`.

## 3. Smoke-check the build

Launch `dist/launcher.exe`. Confirm the dark Sun Valley theme renders (not the
pale `clam` fallback), the top bar / status bar appear, and toggling to light and
back works. Load a copy of a save and confirm the Info summary populates.
