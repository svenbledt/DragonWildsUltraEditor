#!/usr/bin/env python3
"""
build_mount_ids.py - rebuild EMBEDDED_MOUNT_TAGS in data/unlock_ids.py from the
ItemDumper mount dump (ItemDumper_mounts.jsonl).

Mounts are unlocked in the save via Character.Mount.MountsUnlockedList, which
holds two kinds of entries:
  * per-variant refs:  "MountDataAsset:DA_Mount_Terrorbird_00_00"
  * a per-type tag:    "TAG.Mounts.Type.Terrorbird"
The dumper enumerates the real MountDataAsset objects and records each one's full
name. This script turns those into the exact "MountDataAsset:<assetname>" unlock
strings, derives the "TAG.Mounts.Type.<Type>" tags from the asset names, unions
everything with what's already known (save files + current embedded list), and
writes the result so the editor's "Unlock all mounts" button matches the game.
"""
import argparse
import json
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))  # repo root
GAME_WIN64 = r"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64"
DUMP_CANDIDATES = [
    os.path.join(HERE, "ItemDumper_mounts.jsonl"),
    os.path.join(GAME_WIN64, "ItemDumper_mounts.jsonl"),
]

# "MountDataAsset /path/DA_Mount_Terrorbird_00_00.DA_Mount_Terrorbird_00_00"
ASSET_NAME_RE = re.compile(r"\.([A-Za-z0-9_]+)$")
# DA_Mount_<Type>_<nn>_<nn>  ->  <Type>
MOUNT_TYPE_RE = re.compile(r"DA_Mount_(.+?)_\d+_\d+$", re.I)
# an already-formed unlock entry we can trust verbatim
DIRECT_RE = re.compile(r"(?i)(^MountDataAsset:|^TAG\.Mounts?\.|Mounts?\.Type\.)")
META_KEYS = {"__class", "__fullname", "PersistenceID"}


def find_dump(explicit):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for c in DUMP_CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def load_records(path):
    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


def asset_name(fullname):
    m = ASSET_NAME_RE.search(fullname or "")
    return m.group(1) if m else None


def tags_from_records(recs):
    """Return (variant_refs, type_tags, per_asset) from MountDataAsset records."""
    variant_refs, type_tags, per_asset = set(), set(), []
    for r in recs:
        cls = r.get("__class", "")
        fn = r.get("__fullname", "")
        # only the real mount assets produce unlock strings
        if "MountDataAsset" not in cls and not fn.startswith("MountDataAsset "):
            continue
        an = asset_name(fn)
        if not an:
            continue
        ref = "MountDataAsset:" + an
        variant_refs.add(ref)
        tt = None
        m = MOUNT_TYPE_RE.search(an)
        if m:
            tt = "TAG.Mounts.Type." + m.group(1)
            type_tags.add(tt)
        # also keep any value that is already a tag/ref inside the record
        for k, v in r.items():
            if k in META_KEYS or not isinstance(v, str):
                continue
            if DIRECT_RE.search(v):
                (type_tags if v.startswith("TAG") else variant_refs).add(v)
        per_asset.append((an, ref, tt))
    return variant_refs, type_tags, per_asset


def known_mount_tags():
    """Mount entries already proven real: current embedded list + all save files."""
    ids = set()
    try:
        sys.path.insert(0, PROJECT)
        import importlib
        import data.unlock_ids
        importlib.reload(data.unlock_ids)
        ids |= set(getattr(data.unlock_ids, "EMBEDDED_MOUNT_TAGS", []))
    except Exception as e:
        print(f"  (could not import data.unlock_ids: {e})")
    savedir = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                           "RSDragonwilds", "Saved", "SaveCharacters")
    for s in glob.glob(os.path.join(savedir, "*.json")):
        try:
            with open(s, encoding="utf-8") as f:
                d = json.load(f)
            gp = d.get("GameProgress", d)
            mount = gp.get("Character", {}).get("Mount", {})
            ids |= set(mount.get("MountsUnlockedList", []))
        except Exception:
            pass
    return ids


def rewrite(mount_tags, path=None):
    """Span-aware rewrite of EMBEDDED_MOUNT_TAGS in data/unlock_ids.py.

    The assignment there is pretty-printed across many lines (one entry per
    line), so we can't just replace a single line: we replace every line from
    the one starting with "EMBEDDED_MOUNT_TAGS = [" through the first
    subsequent line whose stripped content ends with "]" (inclusive), with a
    single new single-line assignment.
    """
    if path is None:
        path = os.path.join(PROJECT, "data", "unlock_ids.py")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    new = "EMBEDDED_MOUNT_TAGS = [" + ", ".join("'" + t + "'" for t in mount_tags) + "]\n"
    out, i, done = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if not done and ln.startswith("EMBEDDED_MOUNT_TAGS ="):
            out.append(new)
            done = True
            while i < len(lines) and not lines[i].strip().endswith("]"):
                i += 1
            i += 1
            continue
        out.append(ln)
        i += 1
    if not done:
        raise RuntimeError("EMBEDDED_MOUNT_TAGS assignment not found in data/unlock_ids.py")
    with open(path + ".bak", "w", encoding="utf-8") as b, open(path, encoding="utf-8") as a:
        b.write(a.read())
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="write even if the dump yielded no MountDataAsset entries")
    args = ap.parse_args()

    dump = find_dump(args.dump)
    if not dump:
        print("ERROR: mount dump not found. Run F8 in-game with the updated mod first.")
        print("Looked in:\n  " + "\n  ".join(DUMP_CANDIDATES))
        sys.exit(1)
    print(f"Reading mount dump: {dump}")
    recs = load_records(dump)
    print(f"Mount records: {len(recs)}")

    variant_refs, type_tags, per_asset = tags_from_records(recs)
    print(f"\nMount variants (MountDataAsset assets): {len(variant_refs)}")
    print("\nPer mount asset -> unlock string:")
    for an, ref, tt in sorted(per_asset):
        print(f"  {an:34} -> {ref}")
    # IMPORTANT: MountsUnlockedList in the save accepts ONLY "MountDataAsset:"
    # ref strings. Type tags (TAG.Mounts.Type.*) are NOT valid entries there -
    # writing them corrupts the save so the game fails to load player state.
    # We derive them for information only and never put them in the list.
    if type_tags:
        print("\n(info only - NOT written; type tags are not valid list entries):")
        for t in sorted(type_tags):
            print(f"  {t}")

    known = known_mount_tags()
    # keep only MountDataAsset refs; drop any stray non-ref (e.g. an old bad
    # type tag left in the embedded list from a previous run)
    final = sorted(r for r in (variant_refs | known) if r.startswith("MountDataAsset:"))
    dropped = sorted(r for r in (variant_refs | known) if not r.startswith("MountDataAsset:"))
    print(f"\nKnown (embedded + saves): {len(known)}")
    if dropped:
        print(f"Dropped {len(dropped)} non-MountDataAsset entr(y/ies): {dropped}")
    print(f"Final EMBEDDED_MOUNT_TAGS -> {len(final)} MountDataAsset refs")

    if not variant_refs and not args.force:
        print("\nNo MountDataAsset entries found in the dump; not writing "
              "(use --force to write known/save entries anyway). "
              "Check that the mod enumerated class 'MountDataAsset'.")
        sys.exit(2)
    if args.dry_run:
        print("\n--dry-run: not writing.")
        return
    rewrite(final)
    print(f"\nRewrote EMBEDDED_MOUNT_TAGS in data/unlock_ids.py ({len(final)} entries), backup .bak")


if __name__ == "__main__":
    main()
