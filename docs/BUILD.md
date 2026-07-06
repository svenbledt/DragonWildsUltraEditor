# Building the DragonWilds Ultra Editor exe

The exe is compiled with **Nuitka** (Python → C → native machine-code binary),
not PyInstaller. Two reasons:

1. **Antivirus.** The old PyInstaller `--onefile` build tripped heuristic AV
   engines (self-extracting bootloader, and UPX packing), which got it flagged
   on VirusTotal and deleted from NexusMods. A Nuitka-compiled binary looks like
   an ordinary native program and is flagged far less often.
2. **Source.** PyInstaller ships your code as `.pyc` inside an extractable
   archive (trivially dumped with `pyinstxtractor` + a decompiler). Nuitka emits
   real compiled code — there is no `.pyc` to extract.

## 1. Prerequisites

- Python 3 with the `py` launcher on PATH.
- A C compiler. Verified with **MSVC** (Visual Studio 2022 Build Tools).
  If MSVC is absent, Nuitka offers to download MinGW-w64 automatically
  (`--assume-yes-for-downloads` accepts this).

## 2. Build

Just run:

```
build_exe.bat
```

It creates an isolated `.venv-build`, installs `requirements.txt` (CustomTkinter
+ Pillow) + Nuitka, compiles `main.py` to a **standalone folder**, and zips it
to `dist\DragonWildsUltraEditor-standalone.zip` (the file you upload to
NexusMods).

We ship the `--standalone` folder rather than a `--onefile` exe on purpose: the
onefile self-extracting stub is what CrowdStrike / Symantec / Elastic ML
heuristics flag as "dropper-like", which got the file auto-quarantined on
NexusMods. The folder form has no stub and is the least likely to be flagged.

To build by hand:

```
py -m nuitka --standalone --enable-plugin=tk-inter --include-package-data=customtkinter ^
   --include-package=ui --include-package=core --include-package=data ^
   --include-data-dir=data/icons=data/icons ^
   --include-data-files=Dragonwilds_Editor.ico=Dragonwilds_Editor.ico ^
   --include-data-files=Dragonwilds_Editor.png=Dragonwilds_Editor.png ^
   --windows-console-mode=disable --windows-icon-from-ico=Dragonwilds_Editor.ico ^
   --company-name="DragonWilds Ultra Editor" ^
   --product-name="DragonWilds Ultra Editor" ^
   --file-description="DragonWilds Ultra Save Editor" ^
   --file-version=13.0.0.0 ^
   --product-version=13.0.0.0 ^
   --assume-yes-for-downloads ^
   --msvc=latest ^
   --output-dir=dist --output-filename=DragonWildsUltraEditor.exe main.py
```

This produces `dist\main.dist\` (rename it to `DragonWildsUltraEditor\` and
zip it for distribution).

Flag notes:

- `--enable-plugin=tk-inter` bundles Tcl/Tk, which CustomTkinter builds on top
  of. Without it the app fails to start.
- `--include-package-data=customtkinter` bundles CustomTkinter's own theme/asset
  files. Without it the frozen app raises on startup.
- `--include-package=ui --include-package=core --include-package=data` force the
  app's own packages in. `ui/app.py` loads pages with
  `importlib.import_module()` from a string table, which Nuitka cannot follow
  statically — without these flags the frozen exe is missing every page module
  and each page falls back to the "Coming soon…" placeholder.
- `--include-data-dir=data/icons=data/icons` bundles the 754-icon item-icon set
  (plus `manifest.json`) used by the inventory/loadout icon grid. Without it the
  grid falls back to blank slots. Regenerate this folder with
  `tools/icon_extractor` after a game update adds new items (see its own
  README/usage notes) — extraction is not part of this build step.
- `--windows-console-mode=disable` suppresses the console window.
- `--standalone` emits a folder (app exe + its DLLs). Adding `--onefile` would
  collapse it into a single exe, but that reintroduces the self-extracting stub
  the AV heuristics dislike — so we don't.
- `tools/game_dump/` (static game-data dumps + generators) is dev-only and is
  NOT imported by `main.py`, so it is never bundled.

## 3. Smoke-check the build

Launch `dist\DragonWildsUltraEditor\DragonWildsUltraEditor.exe`. Confirm the
character picker lists real save files, opening one shows the sidebar UI with
its six pages, item icons render in the inventory/loadout grid (confirms
`data\icons` was bundled), Save writes a `.bak-*` backup, and the theme toggle
persists across restart.

## 4. If AV still flags it

Native compilation removes the biggest triggers, but an unsigned binary still
starts from zero reputation. Remaining levers, in order:

1. Ship the `--standalone` folder (zipped) instead of `--onefile`.
2. Submit the file as a false positive to the flagging vendor (Microsoft's
   Security Intelligence submission portal is fast and free).
3. Authenticode code-signing (OV cert, or a free OSS route like SignPath) —
   the real long-term fix; builds reputation so future releases pass cleanly.
