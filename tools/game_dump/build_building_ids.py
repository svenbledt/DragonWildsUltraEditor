#!/usr/bin/env python3
"""
build_building_ids.py - rebuild EMBEDDED_BUILDING_IDS in data/unlock_ids.py from the
ItemDumper building dump (ItemDumper_buildings.jsonl).

Build pieces are unlocked in the save via Progress.BuildingsUnlocked - a SEPARATE
asset class / id namespace from items and recipes (verified: zero overlap). The
mod scans many candidate class names, so the dump may include an accidental
non-building class. This converter is deliberately conservative because a single
unrecognized id in BuildingsUnlocked corrupts the save under
dom.PersistenceStrictMode:1 (exactly like recipes):

  1. CONFIRM the real building class(es) by overlap with what your saves already
     have in BuildingsUnlocked (a class whose dumped ids show up as unlocked
     buildings in a real save IS the building class). Falls back to name-based
     detection only if no save is available.
  2. Strip dev/test/deprecated junk by ASSET FOLDER (/Test/, /Deprecated/, ...),
     the same version-proof filter the recipe converter uses (NO count threshold).
  3. Union with ids proven-real by your saves so we never drop a real building.
"""
import argparse
import json
import os
import re
import sys
import glob

# Same folder-junk filter as recipes: dev/removed asset folders are never
# shippable, no matter how many real buildings a future update adds.
JUNK_RE = re.compile(
    r"(?i)(/|_|\b)(test|alphatest|deprecat|depreciat|delet|debug|dummy|"
    r"placeholder|prototype|futuremajorversion|sandbox|scratch|/dev/|example)")

# If no save is available to confirm the class, fall back to class/path names
# that clearly denote buildings.
NAME_HINT_RE = re.compile(r"(?i)(build|buildable|construct|structure|placeable)")

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))  # repo root
GAME_WIN64 = r"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64"
DUMP_CANDIDATES = [
    os.path.join(HERE, "ItemDumper_buildings.jsonl"),
    os.path.join(GAME_WIN64, "ItemDumper_buildings.jsonl"),
]


def find_dump(explicit):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for c in DUMP_CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def load_records(path):
    """Return {pid: record} keeping the first record seen per PersistenceID."""
    recs = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = r.get("PersistenceID")
            if isinstance(pid, str):
                recs.setdefault(pid, r)
    return recs


def path_of(rec):
    fn = rec.get("__fullname", "") if rec else ""
    return fn.split(" ", 1)[1] if " " in fn else fn


def saves_buildings():
    """Building ids already proven real: every save's BuildingsUnlocked."""
    ids = set()
    savedir = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                           "RSDragonwilds", "Saved", "SaveCharacters")
    for s in glob.glob(os.path.join(savedir, "*.json")):
        try:
            with open(s, encoding="utf-8") as f:
                d = json.load(f)
            gp = d.get("GameProgress", d)
            ids |= set(gp.get("Progress", {}).get("BuildingsUnlocked", []))
        except Exception:
            pass
    return ids


def embedded_buildings():
    try:
        sys.path.insert(0, PROJECT)
        import importlib
        import data.unlock_ids
        importlib.reload(data.unlock_ids)
        return set(getattr(data.unlock_ids, "EMBEDDED_BUILDING_IDS", []))
    except Exception as e:
        print(f"  (could not import data.unlock_ids: {e})")
        return set()


def rewrite(building_ids, path=None):
    """Span-aware rewrite of EMBEDDED_BUILDING_IDS in data/unlock_ids.py.

    The assignment there is pretty-printed across many lines (one id per
    line), so we can't just replace a single line: we replace every line from
    the one starting with "EMBEDDED_BUILDING_IDS = [" through the first
    subsequent line whose stripped content ends with "]" (inclusive), with a
    single new single-line assignment.
    """
    if path is None:
        path = os.path.join(PROJECT, "data", "unlock_ids.py")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    new = "EMBEDDED_BUILDING_IDS = [" + ", ".join("'" + i + "'" for i in building_ids) + "]\n"
    out, i, done = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if not done and ln.startswith("EMBEDDED_BUILDING_IDS ="):
            out.append(new)
            done = True
            while i < len(lines) and not lines[i].strip().endswith("]"):
                i += 1
            i += 1
            continue
        out.append(ln)
        i += 1
    if not done:
        raise RuntimeError("EMBEDDED_BUILDING_IDS assignment not found in data/unlock_ids.py")
    with open(path + ".bak", "w", encoding="utf-8") as b, open(path, encoding="utf-8") as a:
        b.write(a.read())
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="write even if no class could be confirmed as buildings")
    args = ap.parse_args()

    dump = find_dump(args.dump)
    if not dump:
        print("ERROR: building dump not found. Run F8 in-game (with the updated "
              "mod) first, then build_item_ids.bat to copy it here.")
        print("Looked in:\n  " + "\n  ".join(DUMP_CANDIDATES))
        sys.exit(1)
    print(f"Reading building dump: {dump}")
    recs = load_records(dump)
    print(f"Building records: {len(recs)} unique PersistenceIDs")

    # group dumped ids by class
    by_class = {}
    for pid, r in recs.items():
        by_class.setdefault(r.get("__class", "?"), set()).add(pid)
    print("By class:")
    for c, s in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
        print(f"  {c:30} {len(s)}")

    proven = saves_buildings()
    print(f"\nProven-real (saves' BuildingsUnlocked): {len(proven)}")

    # 1) CONFIRM the building class(es)
    if proven:
        confirmed = {c: s for c, s in by_class.items()
                     if len(s & proven) >= max(10, 0.02 * len(proven))}
        how = "save overlap"
    else:
        # no save to confirm against - fall back to class/path name hints
        confirmed = {c: s for c, s in by_class.items()
                     if NAME_HINT_RE.search(c)
                     or any(NAME_HINT_RE.search(path_of(recs[p])) for p in list(s)[:5])}
        how = "name hint (no save to confirm against)"

    if confirmed:
        print(f"\nConfirmed building class(es) via {how}:")
        for c, s in sorted(confirmed.items(), key=lambda kv: -len(kv[1])):
            print(f"  {c:30} {len(s)} ids  ({len(s & proven)} match saves)")
    else:
        print("\nWARNING: could not confirm any class as buildings. "
              "Check the 'By class' list above / diagnostics for the real name.")
        if not args.force:
            print("Not writing (use --force to write proven-real save ids only).")
            if args.dry_run:
                return
            sys.exit(2)

    candidate = set().union(*confirmed.values()) if confirmed else set()

    # 2) strip folder-junk (version-proof)
    junk = {p for p in candidate if JUNK_RE.search(path_of(recs.get(p, {})))}
    junk_names = sorted(path_of(recs[p]).rsplit("/", 1)[-1].rsplit(".", 1)[0] for p in junk)

    # 3) union with proven-real + current embedded so we never lose a building
    final = sorted((candidate - junk) | proven | embedded_buildings())

    print(f"\nDropped {len(junk)} dev/test/deprecated building(s) (by asset folder):")
    for nm in junk_names[:15]:
        print(f"    {nm}")
    if len(junk_names) > 15:
        print(f"    ... and {len(junk_names) - 15} more")
    print(f"\nFinal EMBEDDED_BUILDING_IDS -> {len(final)} buildings "
          f"(confirmed class union proven, folder-junk stripped)")

    if args.dry_run:
        print("\n--dry-run: not writing.")
        return
    rewrite(final)
    print(f"Rewrote EMBEDDED_BUILDING_IDS in data/unlock_ids.py ({len(final)}), backup .bak")


if __name__ == "__main__":
    main()
