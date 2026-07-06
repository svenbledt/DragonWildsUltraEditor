# icon_extractor — item icon PNGs straight from the paks (DEV-ONLY, not shipped)

Exports 64x64 PNG icons for `data/item_ids.py` catalog items, keyed by
`PersistenceID`, into `data/icons/` + `data/icons/manifest.json`. The app
itself (`ui/icons.py`) only ever reads `manifest.json`; it works fine with
zero icons present (falls back to a text tile), so this tool is purely a
data-refresh utility, never a build dependency.

Two modes, run in this order every time (see `Program.cs`):

## 1. static (primary, default)

Reads each item's own cooked DataAsset directly from the game's IoStore
paks via [CUE4Parse] and follows its **real** icon reference - no in-game
roaming, no dependence on whether the item happened to be "loaded" when a
dump was taken.

How it works (verified 2026-07-06 against RSDragonwilds / `GAME_UE5_6`):

* Every item is one `.uasset` package (`ItemData`/`EquipmentData`/... or a
  Blueprint CDO like `BP_Consumables_Food_C`), located under one of several
  content roots (`/Game/...`, `/UmbralSands/...`, `/Fishing/...`,
  `/DowdunReach/...` - one per installed content plugin/DLC). Its in-pak path
  is always `<Root>/Content/<same relative path as the /Root/ alias>.uasset`
  regardless of which root, so a root-agnostic reverse lookup keyed on the
  path *after* `.../Content/` (case-insensitive) resolves all of them
  uniformly (`ItemIconDiscovery.BuildContentPathIndex` /
  `ResolvePackagePath`).
* The per-item relative path comes from `tools/ue4ss_dumper/ItemDumper_items.jsonl`'s
  `__fullname` field (`"ItemData /Game/Foo/Bar.Bar"`), produced by an earlier
  in-game F8 dump for essentially every item in `data/item_ids.py` - that
  file just was never previously used for icon lookup.
* `PersistenceID` is a plain `StrProperty` on the export - **already** the
  exact url-safe-base64 string used everywhere else in this app. There is no
  FGuid decode/encode step anywhere in this pipeline (round-tripped and
  confirmed via Abraxus Ring: `TuG7zUS90qgd7BOHhOxd8Q`).
* The icon is a `SoftObjectProperty` named `Icon` (checked with fallback
  names `IconFile`/`IconTexture`) whose `FSoftObjectPath.AssetPathName` is
  the texture's own package path - present and resolvable in the cooked data
  even though nothing is "loaded" at cook time. That's exactly why this
  works for items the in-game dump recorded `IconFile == ""` for (item was
  never loaded that session).
* A small number of item classes (observed on `BP_Consumables_RecipeUnlocker2_C`
  pattern-unlockers and `BP_Consumables_SkillTome_C` tomes - e.g. "Bramblemead
  Cape", "Tome of the Titan") never serialize a `PersistenceID` tag on their
  export at all (it's produced some other way at runtime, not stored in the
  cooked asset). When a package holds exactly one export carrying an `Icon`
  soft reference, that's unambiguously *this* item's data (one item per
  `.uasset` file, true across the whole catalog), so it's used directly as a
  fallback match.
* Some textures are BC/ASTC/ETC-compressed and need CUE4Parse-Conversion's
  managed "Detex" decoder, which embeds a native `Detex.dll` as a resource
  but does not auto-load it. `Program.InitDetex()` extracts that resource to
  a temp file and calls `DetexHelper.Initialize(path)` once at startup;
  without this step, ~40 textures fail with `"Detex decompression failed:
  not initialized"`.

Result (2026-07-06 run): **1384 / 1385** catalog items now have a real icon
(up from 754). The one residual - "Anima Orb" - genuinely has no `Icon`
property in the cooked asset at all (placeholder mesh, dev/quest item); that
is expected, not a bug.

## 2. iconlist (fallback)

The original approach: matches PNG stems named in `iconlist.txt` (built by
`make_iconlist.py` from `data/item_ids.py`'s `IconFile` field, e.g.
`T_Icon_Runic_Ring.png`) against texture filenames found anywhere in the
paks. Kept as a safety net for any PID the static pass still can't resolve;
it never overwrites a PID the static pass already found.

## Merging

Both passes read the **existing** `data/icons/manifest.json` first and only
add/overwrite entries they actually resolve - existing entries are never
dropped, even if a later run can't re-derive them (e.g. paks unavailable).

## Prerequisites

1. **.NET 10 SDK** (CUE4Parse `1.2.2.202607` targets `net10.0`).
2. A **`Mappings.usmap`** for the game (F9 / `dump_usmap` in-game via the
   ItemDumper UE4SS mod - see `tools/ue4ss_dumper/README.md`).
3. `tools/ue4ss_dumper/ItemDumper_items.jsonl` present (already checked into
   the repo; regenerate via the F8 in-game dump after a game update).

## Run

```
dotnet run -c Release
```

Args (all optional, positional): `[paksDir] [usmapPath] [iconlistPath]
[outDir] [onlyStem] [mode] [itemsJsonlPath]`. Defaults point at the local
Steam install, `tools/icon_extractor/iconlist.txt`, `data/icons/`, `static`
mode, and `tools/ue4ss_dumper/ItemDumper_items.jsonl`, respectively. Pass
`mode=iconlist` to run only the legacy stem-match pass (e.g. for a quick
top-up without remounting for a static re-scan of every item).

[CUE4Parse]: https://github.com/FabianFG/CUE4Parse
