# game_dump - static game-data dumps + editor data generators (dev-only)

Everything the editor knows about the game's items, recipes, buildings and
mounts comes from here. The dumps are extracted **statically from the game
paks** with CUE4Parse (`tools/icon_extractor --dump-data`) - no UE4SS mod, no
running game. This replaced the old `tools/ue4ss_dumper` runtime (F8 in-game)
dumper entirely.

## Refreshing after a game update

```
cd tools/icon_extractor
dotnet run -c Release -- --dump-data      # rewrites the *.jsonl files here
cd ../game_dump
py build_item_ids.py                      # data/item_ids.py      (item catalog, merge)
py build_pickup_ids.py                    # data/pickup_ids.py    (Picked-up Items unlocker)
py build_recipe_ids.py                    # data/unlock_ids.py    EMBEDDED_RECIPE_IDS
py build_building_ids.py                  # data/unlock_ids.py    EMBEDDED_BUILDING_IDS
py build_mount_ids.py                     # data/unlock_ids.py    EMBEDDED_MOUNT_TAGS
py build_shrine_ids.py                    # data/shrine_ids.py    (static, rarely changes)
py build_doctor_ids.py                    # data/doctor_ids.py    (run LAST - after the good sets)
py -m pytest ../../tests -q
```

Each builder prints an analysis and backs up the file it rewrites (`.bak`).
All support `--dry-run`.

## The dumps (ItemDumper_*.jsonl)

One JSON object per data asset. Key fields:

- `PersistenceID` - the id the save file uses (resolved through the asset's
  blueprint-CDO template chain when not authored on the asset itself).
- `__fullname` - `<ExportClass> <asset path>.<asset name>`.
- `__registered` - **the important one.** True iff the asset lives under the
  matching Dominion subsystem's `+DataPaths` folders in the game's own
  `RSDragonwilds/Config/DefaultGame.ini`. The game registers ONLY those
  assets; one unregistered id in a save's unlock list aborts the whole
  character load under `dom.PersistenceStrictMode:1` ("Unknown id ..." ->
  CharCantLoad). Mounts use the AssetManager scan dirs instead (plugin
  mounts register at runtime via GameFeatureData, so `__registered:false`
  mounts are still real).
- `SourceString` / `Name` - authored English display name (cooked FText,
  falling back to string tables and Game.locres for the stragglers).
- `Weight`, `Durability`, `PowerLevel`, `MaxStackSize`, `VitalShield`,
  `Category` - when present on the asset.

Current counts (game 0.12.0.9): 1392 items, 1103+7 recipes (1091 unlockable
after dropping /Deleted/ + AlphaTest dead content), 772 buildings, 21 mounts.

## What is "junk"?

- **recipes**: unregistered (the 7 RECIPE_TEST in /Game/Gameplay/test/) plus
  registered-but-dead content (/Deleted/ folders, the AlphaTest cape).
  /Deprecated/-folder recipes are deliberately registered by the game
  (AlwaysCook) and ARE unlockable - do not filter them by name.
- **buildings**: unregistered only. The two BUILDPIECE_DEPRECATED_* pieces
  are registered and real.
- **pickups**: `breaks_load()` = unregistered or dead/dev folders (incl.
  /AlwaysCook/, where the load-breaking Fire Cape vestige lives) - these go
  in the Save doctor blocklist. The unlocker additionally skips
  placeholder/broken-name items ([PH], (Expired), empty name), which are
  harmless in a save but not real obtainable items.
