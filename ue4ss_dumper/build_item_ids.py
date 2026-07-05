#!/usr/bin/env python3
"""
build_item_ids.py - update item_ids.py for the DragonWilds Ultra Editor from the
ItemDumper UE4SS dump (ItemDumper_items.jsonl).

MERGE model (important):
  * Existing entries (matched by PersistenceID) are kept EXACTLY as-is. The game
    reports item names localized to the user's language (e.g. German), so we must
    not overwrite the curated English names / fields already in item_ids.py.
  * Only genuinely NEW PersistenceIDs (not already in item_ids.py) are appended.
    Their name comes from the asset path (__fullname, language-neutral) when
    possible, else the localized Name.

Workflow (see build_item_ids.bat):
  1. In-game, load a world and press F8 -> produces ItemDumper_items.jsonl.
  2. Run this script. It prints an analysis and, unless --dry-run, writes a new
     item_ids.py (old one backed up to item_ids.py.bak).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)  # item_ids.py lives one level up
GAME_WIN64 = r"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64"
DEFAULT_DUMP_CANDIDATES = [
    os.path.join(HERE, "ItemDumper_items.jsonl"),
    os.path.join(GAME_WIN64, "ItemDumper_items.jsonl"),
    os.path.join(GAME_WIN64, "ue4ss", "ItemDumper_items.jsonl"),
]

# The game's Name property carries the clean localized display name (English
# when the game is set to English). Prefer it; fall back to the asset path only
# when Name is empty.
NAME_FIELDS = ["Name", "DisplayName", "ItemName", "SourceString"]

# Dev/removed assets that live in the build but are not real player items.
# Matched against the asset path (__fullname). Filtered from NEW items only.
JUNK_RE = re.compile(r"(/Deleted/|Deprecated|_Test|Placeholder|DebugOnly|DoNotUse)", re.I)


def find_dump(explicit):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for c in DEFAULT_DUMP_CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def load_records(path):
    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  ! skipping bad JSON on line {ln}: {e}")
    return recs


def name_from_fullname(fn):
    """'...ItemData_SteelSword.0' / '...HeldEquipmentData /Game/.../Steel_Sword.Steel_Sword'
    -> a readable English-ish name."""
    if not fn:
        return None
    # take the token after the last / and strip the trailing .Something
    tail = re.split(r"[\\/]", str(fn))[-1]
    tail = tail.split(".")[0]
    # drop common asset prefixes
    tail = re.sub(r"^(ItemData_|BP_|DA_|Item_|Held|Equipment)", "", tail)
    tail = tail.strip("_")
    if not tail:
        return None
    # CamelCase / snake_case -> spaced words
    tail = tail.replace("_", " ")
    tail = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", tail)
    return tail.strip()


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def new_entry(rec):
    pid = rec.get("PersistenceID")
    if not pid or not isinstance(pid, str):
        return None
    # prefer the game's display name; fall back to the asset path only if empty
    name = None
    for nf in NAME_FIELDS:
        if rec.get(nf):
            name = str(rec[nf])
            break
    if not name:
        name = name_from_fullname(rec.get("__fullname"))
    if not name:
        name = pid

    entry = {"SourceString": name, "PersistenceID": pid}
    w = num(rec.get("Weight"))
    entry["Weight"] = w if w is not None else 1.0
    for src in ("Durability", "PowerLevel"):
        if rec.get(src) is not None:
            n = num(rec[src])
            if n is not None:
                entry[src] = int(n) if float(n).is_integer() else n
    ms = num(rec.get("MaxStackSize", rec.get("MaxStack", rec.get("StackSize"))))
    entry["MaxStackSize"] = int(ms) if ms is not None else 1
    vs = num(rec.get("VitalShield"))
    entry["VitalShield"] = int(vs) if vs is not None else 0
    entry["IconFile"] = ""
    entry["Category"] = str(rec.get("Category") or "Basic Item")
    entry["GUIDs"] = []
    return entry


def load_existing():
    try:
        sys.path.insert(0, PROJECT)
        import importlib
        import item_ids
        importlib.reload(item_ids)
        return list(item_ids.ITEM_LIST)
    except Exception as e:
        print(f"  (could not import existing item_ids.py: {e})")
        return []


def serialize_value(v):
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, bool):
        return "True" if v else "False"
    return repr(v)


def write_item_ids(entries, out_path):
    lines = ["ITEM_LIST = [\n"]
    for e in entries:
        lines.append("    {\n")
        items = list(e.items())
        for i, (k, v) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            lines.append(f'        "{k}": {serialize_value(v)}{comma}\n')
        lines.append("    },\n")
    lines.append("]\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", help="path to ItemDumper_items.jsonl")
    ap.add_argument("--dry-run", action="store_true", help="analyze only, do not write")
    ap.add_argument("--force", action="store_true", help="write even if dump looks thin")
    ap.add_argument("--include-junk", action="store_true",
                    help="also add deprecated/deleted/test dev assets")
    args = ap.parse_args()

    dump = find_dump(args.dump)
    if not dump:
        print("ERROR: dump file not found. Run the F8 dump in-game first.")
        print("Looked in:\n  " + "\n  ".join(DEFAULT_DUMP_CANDIDATES))
        sys.exit(1)
    print(f"Reading dump: {dump}")
    recs = load_records(dump)
    print(f"Records in dump: {len(recs)}")
    if not recs:
        sys.exit(1)

    # class breakdown
    by_class = {}
    for r in recs:
        by_class[r.get("__class", "?")] = by_class.get(r.get("__class", "?"), 0) + 1
    print("\nDumped classes:")
    for c, n in sorted(by_class.items(), key=lambda kv: -kv[1]):
        print(f"  {c:24} {n}")

    dump_pids = {}
    for r in recs:
        pid = r.get("PersistenceID")
        if isinstance(pid, str):
            dump_pids.setdefault(pid, r)
    print(f"\nUnique PersistenceIDs in dump: {len(dump_pids)}")

    existing = load_existing()
    existing_pids = {e.get("PersistenceID") for e in existing}
    print(f"Current item_ids.py entries:   {len(existing)}")

    new_pids = [p for p in dump_pids if p not in existing_pids]
    missing_from_dump = [e for e in existing if e.get("PersistenceID") not in dump_pids]

    junk_pids = []
    if not args.include_junk:
        kept_new = []
        for p in new_pids:
            if JUNK_RE.search(dump_pids[p].get("__fullname", "")):
                junk_pids.append(p)
            else:
                kept_new.append(p)
        new_pids = kept_new

    print(f"\n  overlap (known items in dump): {len(dump_pids) - len(new_pids) - len(junk_pids)}")
    print(f"  NEW items (to be appended):    {len(new_pids)}")
    if junk_pids:
        print(f"  junk skipped (deprecated/test):{len(junk_pids)}  (use --include-junk to keep)")
    print(f"  known items NOT in this dump:   {len(missing_from_dump)}  (kept untouched)")

    new_entries = []
    for p in new_pids:
        e = new_entry(dump_pids[p])
        if e:
            new_entries.append(e)
    if new_entries:
        print("\nNew items to be added:")
        for e in new_entries:
            g = dump_pids[e["PersistenceID"]].get("Name", "")
            print(f"  + {e['SourceString']:30} [{e['PersistenceID']}]  (game: {g})")

    if args.dry_run:
        print("\n--dry-run: not writing. Re-run without --dry-run to apply.")
        return
    if not new_entries and not args.force:
        print("\nNo new items to add - item_ids.py already covers this dump. "
              "(Nothing written.)")
        return

    merged = list(existing) + new_entries
    out = os.path.join(PROJECT, "item_ids.py")
    if os.path.isfile(out):
        with open(out, "r", encoding="utf-8") as a, open(out + ".bak", "w", encoding="utf-8") as b:
            b.write(a.read())
        print(f"\nBacked up -> {out}.bak")
    write_item_ids(merged, out)
    print(f"Wrote {len(merged)} items ({len(new_entries)} new) -> {out}")


if __name__ == "__main__":
    main()
