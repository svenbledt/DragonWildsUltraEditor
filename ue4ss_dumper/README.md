# ItemDumper — regenerate item_ids.py and the recipe list from the live game

This folder holds a small UE4SS Lua mod plus helper scripts that dump the game's
complete item list **and recipe list** straight out of memory, so `item_ids.py`
and the recipe unlocker's `EMBEDDED_RECIPE_IDS` can be rebuilt after any
Dragonwilds update (including content you haven't unlocked yet).

Recipes are a **separate asset class** from items (their PersistenceIDs live in a
different id namespace — zero overlap with item IDs), so they get their own dump
file (`ItemDumper_recipes.jsonl`) and their own converter (`build_recipe_ids.py`).

**Mounts** are unlocked in the save via `Character.Mount.MountsUnlockedList`,
which holds ONLY per-variant refs of the form `MountDataAsset:<assetname>`
(e.g. `MountDataAsset:DA_Mount_Terrorbird_00_00`). The dumper enumerates the
`MountDataAsset` objects (`ItemDumper_mounts.jsonl`) and `build_mount_ids.py`
builds those exact ref strings into `EMBEDDED_MOUNT_TAGS` in `tab_extra.py`,
powering the "Unlock all mounts" button.

> ⚠️ Do NOT put `TAG.Mounts.Type.*` gameplay tags in `MountsUnlockedList` -
> they are not valid entries and corrupt the save (the game then fails to load
> player state). `build_mount_ids.py` and the editor both hard-filter to
> `MountDataAsset:` refs for this reason.

**Buildings** are unlocked via `Progress.BuildingsUnlocked` — a **separate id
namespace** from both items and recipes (zero overlap). The dumper scans for the
building asset class (`ItemDumper_buildings.jsonl`) and `build_building_ids.py`
builds `EMBEDDED_BUILDING_IDS` in `tab_extra.py`, powering the "Unlock all
buildings" button. Because the class name isn't known up front, the mod probes
many candidate names; the converter then **confirms** the real building class by
overlap with your saves' `BuildingsUnlocked` (so an accidental non-building match
is discarded) and strips dev/removed junk by asset folder — the same
strict-mode-safe filter used for recipes (see the recipe warning below).

> ⚠️ Like recipes, `BuildingsUnlocked` is validated under
> `dom.PersistenceStrictMode:1`: a single unrecognized id aborts the character
> load. Never write an unconfirmed id into it. Junk is filtered by asset FOLDER
> (`/Test/`, `/Deprecated/`, …), which is version-proof — do NOT gate on list
> size (a future update may legitimately ship more recipes/buildings).

One F8 press dumps all four (items, recipes, mounts, buildings).

## Layout
- `ItemDumper/` — the UE4SS mod (source of truth, lives in the project).
  - `enabled.txt`, `scripts/main.lua`
- `setup_dumper_link.bat` — (re)creates the junction into the game's UE4SS `Mods`
  folder. The project is on `C:` and the game on `F:`, so a real hardlink is
  impossible (hardlinks can't cross drives); a **directory junction** is used
  instead — same effect: edits in the project appear instantly in the game.
- `build_item_ids.py` / `build_item_ids.bat` — turn the dump into `item_ids.py`.

## One-time / after-every-update
1. Run `setup_dumper_link.bat` (recreates `…\ue4ss\Mods\ItemDumper` -> this folder).
   Not needed unless the update wiped the Mods folder.
2. Fully restart the game (UE4SS hot-reload is off, so a new mod only loads on
   launch).

## To dump
1. Load into a world with some items in your inventory.
2. Press **F8** (or open the console and run `dump_items`).
   Writes to `…\Binaries\Win64\ue4ss\`:
   - `ItemDumper_items.jsonl` — one JSON object per item
   - `ItemDumper_diagnostics.txt` — class chain + per-class counts (for debugging)
3. Run `build_item_ids.bat` — copies the dump here and prints an analysis
   (record count, new vs. known items, name-match check). If it looks right,
   run `py build_item_ids.py` to write the new `item_ids.py` (old one is backed
   up to `item_ids.py.bak`).
