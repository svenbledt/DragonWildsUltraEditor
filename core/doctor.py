"""Save doctor: detect and repair known save-breaking states.

Under dom.PersistenceStrictMode:1 a single unrecognized id in an unlock
list aborts the whole character load (CharCantLoad) — e.g. the Fire Cape
AlwaysCook vestige in ItemsPickedUp, dev/test recipe ids written by older
editor versions, or type-tagged mount refs in MountsUnlockedList.

Every repair is removal of KNOWN-BAD entries only (generated blocklists in
data/doctor_ids.py, plus the verified mount ref set) — ids the game itself
wrote are never touched, so a healthy save is never modified.
"""
from core.unlocks import ALL_MOUNT_REFS
from data.doctor_ids import (
    BAD_PICKUP_IDS, BAD_RECIPE_IDS, BAD_BUILDING_IDS,
)

_BAD_SETS = {
    "ItemsPickedUp": frozenset(BAD_PICKUP_IDS),
    "RecipesUnlocked": frozenset(BAD_RECIPE_IDS),
    "RecipesNew": frozenset(BAD_RECIPE_IDS),
    "BuildingsUnlocked": frozenset(BAD_BUILDING_IDS),
    "BuildingPiecesNew": frozenset(BAD_BUILDING_IDS),
}

_DEDUP_LISTS = ("ItemsPickedUp", "RecipesUnlocked", "RecipesNew",
                "BuildingsUnlocked", "BuildingPiecesNew", "ShrinesUnlocked")


def _progress_list(sf, key):
    prog = sf.progress.get("Progress")
    lst = prog.get(key) if isinstance(prog, dict) else None
    return lst if isinstance(lst, list) else None


def _mount_list(sf):
    character = sf.progress.get("Character")
    mount = character.get("Mount") if isinstance(character, dict) else None
    lst = mount.get("MountsUnlockedList") if isinstance(mount, dict) else None
    return lst if isinstance(lst, list) else None


def _scan_bad_ids(sf):
    findings = []
    for key, bad in _BAD_SETS.items():
        lst = _progress_list(sf, key)
        if lst:
            hits = [i for i in lst if i in bad]
            if hits:
                findings.append("{}: {} known-bad id(s), e.g. {}".format(
                    key, len(hits), hits[0]))
    return findings


def _fix_bad_ids(sf):
    removed = 0
    for key, bad in _BAD_SETS.items():
        lst = _progress_list(sf, key)
        if lst:
            kept = [i for i in lst if i not in bad]
            removed += len(lst) - len(kept)
            lst[:] = kept
    return removed


def _scan_mounts(sf):
    lst = _mount_list(sf)
    if not lst:
        return []
    bad = [m for m in lst if m not in ALL_MOUNT_REFS]
    return ["MountsUnlockedList: {} invalid ref(s), e.g. {!r}".format(
        len(bad), bad[0])] if bad else []


def _fix_mounts(sf):
    lst = _mount_list(sf)
    if not lst:
        return 0
    kept = [m for m in lst if m in ALL_MOUNT_REFS]
    removed = len(lst) - len(kept)
    lst[:] = kept
    return removed


def _quest_entries(sf):
    qp = sf.progress.get("QuestProgress")
    entries = qp.get("Quests") if isinstance(qp, dict) else None
    return entries if isinstance(entries, list) else []


def _null_objective_entries(sf):
    # QuestObjective is an FName string; 'no objective' is "None". A JSON
    # null (written by older editor versions) makes the game drop the
    # entry / corrupt the quest log on load.
    return [e for e in _quest_entries(sf)
            if isinstance(e, dict) and "QuestObjective" in e
            and not isinstance(e["QuestObjective"], str)]


def _scan_quest_objectives(sf):
    bad = _null_objective_entries(sf)
    return ["Quests: {} entr{} with a null objective, e.g. QuestId {}".format(
        len(bad), "ies" if len(bad) != 1 else "y",
        bad[0].get("QuestId"))] if bad else []


def _fix_quest_objectives(sf):
    bad = _null_objective_entries(sf)
    for e in bad:
        e["QuestObjective"] = "None"
    return len(bad)


def _scan_duplicates(sf):
    findings = []
    lists = [(k, _progress_list(sf, k)) for k in _DEDUP_LISTS]
    lists.append(("MountsUnlockedList", _mount_list(sf)))
    for key, lst in lists:
        if lst:
            dupes = len(lst) - len(set(lst))
            if dupes:
                findings.append("{}: {} duplicate entr{}".format(
                    key, dupes, "ies" if dupes != 1 else "y"))
    return findings


def _fix_duplicates(sf):
    removed = 0
    lists = [_progress_list(sf, k) for k in _DEDUP_LISTS]
    lists.append(_mount_list(sf))
    for lst in lists:
        if lst:
            seen, kept = set(), []
            for i in lst:
                if not (isinstance(i, str) and i in seen):
                    kept.append(i)
                    if isinstance(i, str):
                        seen.add(i)
            removed += len(lst) - len(kept)
            lst[:] = kept
    return removed


CHECKS = [
    {"key": "bad_ids",
     "title": "Dev/removed ids in unlock lists",
     "explain": "Ids of dev, test or deleted assets (e.g. the Fire Cape "
                "vestige in Picked-up items). One of these aborts loading "
                "the character.",
     "scan": _scan_bad_ids, "fix": _fix_bad_ids},
    {"key": "mounts",
     "title": "Invalid mount references",
     "explain": "MountsUnlockedList accepts only the game's known "
                "MountDataAsset: refs — anything else corrupts the save.",
     "scan": _scan_mounts, "fix": _fix_mounts},
    {"key": "quest_objectives",
     "title": "Null quest objectives",
     "explain": "QuestObjective must be a string (\"None\" when empty). A "
                "JSON null — written by older editor versions — makes the "
                "game drop the quest entry or roll the save back on load.",
     "scan": _scan_quest_objectives, "fix": _fix_quest_objectives},
    {"key": "duplicates",
     "title": "Duplicate unlock entries",
     "explain": "The same id listed more than once in an unlock list.",
     "scan": _scan_duplicates, "fix": _fix_duplicates},
]


def scan(sf):
    """[{key,title,explain,details}] — one row per check that found issues."""
    report = []
    for c in CHECKS:
        details = c["scan"](sf)
        if details:
            report.append({"key": c["key"], "title": c["title"],
                           "explain": c["explain"], "details": details})
    return report


def fix(sf, key):
    """Repair one check. Returns how many entries were removed."""
    for c in CHECKS:
        if c["key"] == key:
            removed = c["fix"](sf)
            if removed:
                sf.mark_dirty()
            return removed
    raise ValueError("Unknown doctor check: {}".format(key))


def fix_all(sf):
    """Repair everything. Returns total entries removed."""
    return sum(fix(sf, c["key"]) for c in CHECKS)
