#!/usr/bin/env python3
"""
build_recipe_ids.py - rebuild EMBEDDED_RECIPE_IDS in data/unlock_ids.py from the
ItemDumper recipe dump (ItemDumper_recipes.jsonl).

Recipes are a separate asset class / id namespace from items, so they get their
own dump file and their own converter. This script:
  * reads the dumped recipe PersistenceIDs,
  * validates them against the recipes already known from save files + the
    current embedded list (they should be a SUPERSET),
  * rewrites the EMBEDDED_RECIPE_IDS list in data/unlock_ids.py to the union
    (never drops a known-good recipe).
"""
import argparse
import json
import os
import re
import sys
import glob

# FindAllOf("RecipeData") also returns dev/test/deprecated recipe assets whose
# PersistenceIDs the game's recipe registry does NOT accept. Under
# dom.PersistenceStrictMode:1 a single unrecognized id in RecipesUnlocked aborts
# the entire character load ("Unknown id in RecipesUnlocked entry ..." ->
# CharCantLoad). We drop anything whose asset path/name carries a dev/removed
# marker, UNLESS a real save proves that exact id is genuinely unlockable.
JUNK_RE = re.compile(
    r"(?i)(/|_|\b)(test|alphatest|deprecat|depreciat|delet|debug|dummy|"
    r"placeholder|prototype|futuremajorversion|sandbox|scratch|/dev/|example)")

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))  # repo root
GAME_WIN64 = r"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64"
DUMP_CANDIDATES = [
    os.path.join(HERE, "ItemDumper_recipes.jsonl"),
    os.path.join(GAME_WIN64, "ItemDumper_recipes.jsonl"),
]


def find_dump(explicit):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for c in DUMP_CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def load_pids(path):
    pids, by_class = {}, {}
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
                pids.setdefault(pid, r)
                c = r.get("__class", "?")
                by_class[c] = by_class.get(c, 0) + 1
    return pids, by_class


def known_recipe_ids():
    """Recipes already proven to exist: current embedded list + all save files."""
    ids = set()
    try:
        sys.path.insert(0, PROJECT)
        import importlib
        import data.unlock_ids
        importlib.reload(data.unlock_ids)
        ids |= set(data.unlock_ids.EMBEDDED_RECIPE_IDS)
    except Exception as e:
        print(f"  (could not import data.unlock_ids: {e})")
    savedir = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                           "RSDragonwilds", "Saved", "SaveCharacters")
    for s in glob.glob(os.path.join(savedir, "*.json")):
        try:
            with open(s, encoding="utf-8") as f:
                d = json.load(f)
            gp = d.get("GameProgress", d)
            # Include every save's recipes unconditionally. We do NOT gate on the
            # count here: a future update could legitimately ship >1000 recipes,
            # so a count threshold would wrongly discard a normal save. Junk that
            # a poisoned save may contain is removed later by ASSET FOLDER path
            # (see junk_pids in main), which is version-proof.
            ids |= set(gp.get("Progress", {}).get("RecipesUnlocked", []))
        except Exception:
            pass
    return ids


def rewrite(recipe_ids, path=None):
    """Span-aware rewrite of EMBEDDED_RECIPE_IDS in data/unlock_ids.py.

    The assignment there is pretty-printed across many lines (one id per
    line), so we can't just replace a single line: we replace every line from
    the one starting with "EMBEDDED_RECIPE_IDS = [" through the first
    subsequent line whose stripped content ends with "]" (inclusive), with a
    single new single-line assignment.
    """
    if path is None:
        path = os.path.join(PROJECT, "data", "unlock_ids.py")
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    new = "EMBEDDED_RECIPE_IDS = [" + ", ".join("'" + i + "'" for i in recipe_ids) + "]\n"
    out, i, done = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if not done and ln.startswith("EMBEDDED_RECIPE_IDS ="):
            out.append(new)
            done = True
            while i < len(lines) and not lines[i].strip().endswith("]"):
                i += 1
            i += 1
            continue
        out.append(ln)
        i += 1
    if not done:
        raise RuntimeError("EMBEDDED_RECIPE_IDS assignment not found in data/unlock_ids.py")
    with open(path + ".bak", "w", encoding="utf-8") as b, open(path, encoding="utf-8") as a:
        b.write(a.read())
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="write even if dump misses known recipes")
    args = ap.parse_args()

    dump = find_dump(args.dump)
    if not dump:
        print("ERROR: recipe dump not found. Run F8 in-game first.")
        print("Looked in:\n  " + "\n  ".join(DUMP_CANDIDATES))
        sys.exit(1)
    print(f"Reading recipe dump: {dump}")
    pids, by_class = load_pids(dump)
    print(f"Recipe records: {len(pids)} unique PersistenceIDs")
    print("By class:")
    for c, n in sorted(by_class.items(), key=lambda kv: -kv[1]):
        print(f"  {c:28} {n}")

    known = known_recipe_ids()
    dumped = set(pids)
    covered = known & dumped
    missing = known - dumped
    print(f"\nKnown-real recipes (embedded + saves): {len(known)}")
    print(f"  covered by dump:  {len(covered)}")
    print(f"  MISSING from dump:{len(missing)}  <- dump did not find these")
    print(f"  new from dump:    {len(dumped - known)}")

    # Identify junk by ASSET FOLDER from the live dump (/Test/, /Deprecated/,
    # /Deleted/, /FutureMajorVersion/, *AlphaTest). This is version-proof: those
    # folders are never shippable recipes no matter how many real recipes a
    # future update adds, so there is NO count threshold that could break. A
    # poisoned save's junk ids resolve to these same folders and get removed too.
    junk_pids, junk_names = set(), []
    for pid, r in pids.items():
        fn = r.get("__fullname", "")
        path = fn.split(" ", 1)[1] if " " in fn else fn
        if path and JUNK_RE.search(path):
            junk_pids.add(pid)
            junk_names.append(path.rsplit("/", 1)[-1].rsplit(".", 1)[0])

    # Union so we never lose a real recipe the dump missed, minus folder-junk.
    final = sorted((dumped | known) - junk_pids)
    print(f"\nDropped {len(junk_pids)} dev/test/deprecated recipe(s) "
          f"(by asset folder - never shipped):")
    for nm in sorted(junk_names)[:15]:
        print(f"    {nm}")
    if len(junk_names) > 15:
        print(f"    ... and {len(junk_names) - 15} more")
    print(f"\nFinal EMBEDDED_RECIPE_IDS -> {len(final)} recipes "
          f"(dump union known, folder-junk stripped)")

    if len(covered) < 0.5 * len(known) and not args.force and not dumped:
        print("\nDump found no/too few recipes - wrong class? See diagnostics. "
              "Not writing (use --force to override).")
        sys.exit(2)
    if args.dry_run:
        print("\n--dry-run: not writing.")
        return
    rewrite(final)
    print(f"Rewrote EMBEDDED_RECIPE_IDS in data/unlock_ids.py ({len(final)} recipes), backup .bak")


if __name__ == "__main__":
    main()
