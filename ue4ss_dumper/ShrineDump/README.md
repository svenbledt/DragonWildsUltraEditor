# ShrineDump — authoritative Sanguine-Urn extractor (DEV-ONLY, not shipped)

Extracts the **complete** set of Sanguine Urns straight from the cooked game
files, so we don't have to roam the whole map in-game. This is how the 18 urn
GUIDs in `../build_shrine_ids.py` (`KNOWN_SHRINE_IDS`) were obtained.

## What it does

Uses [CUE4Parse] to mount the IoStore paks and, with a `.usmap` mappings file,
deserialize every `.umap` level package. For each `BP_HealthShrine_C` actor it
reads the `UniqueShrineIdentifier` FGuid and formats it `%08X%08X%08X%08X`
(A/B/C/D) — exactly the string the game writes to `Progress.ShrinesUnlocked`.

Self-validation: all 8 GUIDs we had previously confirmed (7 save-harvested + the
in-game-verified `186B64E2…`) reappear in the extracted set, proving the parse
and byte-order are correct. Two scans (all `/maps/` packages, then all `.umap`
packages) both returned exactly 18 with 0 errors.

## Prerequisites

1. **.NET 10 SDK** (CUE4Parse `1.2.2.202607` targets `net10.0`).
2. A **`Mappings.usmap`** for the game. Generate it with the UE4SS ItemDumper
   mod: launch the game and press **F9** (or console `dump_usmap`) — it calls
   UE4SS's `DumpUSMAP()` and writes `Mappings.usmap` into
   `…/RSDragonwilds/Binaries/Win64/ue4ss/`.

## Run

```
dotnet run -c Release -- \
  "<...>/RSDragonwilds/Content/Paks" \
  "<...>/RSDragonwilds/Binaries/Win64/ue4ss/Mappings.usmap" \
  shrines.jsonl \
  GAME_UE5_6
```

Args: `[paksDir] [usmapPath] [outFile] [EGame]`. **`GAME_UE5_6` is the correct
version for this game** — `GAME_UE5_4/5_5` mount the container but throw
`VersionException` on the actor cells. Append a 5th arg `DISCOVER` to dump path
keywords / sample cell exports instead of extracting.

Output is one JSON line per urn:
`{"PersistenceID":"<32-hex>","__class":"BP_HealthShrine_C"}` — the same format
the F6 accumulator writes, so it drops straight into `../ItemDumper_urns.jsonl`
for `build_shrine_ids.py`.

## Folding results back in

```
cp shrines.jsonl ue4ss_dumper/ItemDumper_urns.jsonl
py ue4ss_dumper/build_shrine_ids.py     # regenerates ../shrine_ids.py
```

If the game updates and adds urns, re-run this (regenerate the usmap first) and
update `KNOWN_SHRINE_IDS`.

[CUE4Parse]: https://github.com/FabianFG/CUE4Parse
