"""Unlock/progress operations: recipes, buildings, pickups, urns, mounts,
map reveal, status reset.

Union-only: existing entries are never removed or reordered. Id sources are
the strict-mode-safe embedded snapshots in data/ — writing any other id can
corrupt the save (the game validates unlock lists).
"""
from data.unlock_ids import (
    EMBEDDED_RECIPE_IDS, EMBEDDED_BUILDING_IDS, EMBEDDED_MOUNT_TAGS,
)
from data.pickup_ids import EMBEDDED_ITEM_PICKUP_IDS
from data.shrine_ids import EMBEDDED_SHRINE_IDS

BASE_MAX_HP = 100
HP_PER_SHRINE = 10

# MountsUnlockedList accepts ONLY bare MountDataAsset: refs — type-tagged
# entries corrupt the save.
ALL_MOUNT_REFS = [t for t in EMBEDDED_MOUNT_TAGS
                  if isinstance(t, str) and t.startswith("MountDataAsset:")]
DEFAULT_MOUNT = next((t for t in ALL_MOUNT_REFS if "Terrorbird" in t),
                     ALL_MOUNT_REFS[0] if ALL_MOUNT_REFS else None)

CATEGORY_LABELS = {
    "recipes": "Recipes",
    "buildings": "Buildings",
    "pickups": "Item compendium",
    "urns": "Sanguine Urns",
    "mounts": "Mounts",
}


def merge_ids(current, ids):
    """Add unseen string ids to `current` in place; returns how many were
    added. Never removes or reorders existing entries."""
    seen = set(current)
    added = 0
    for i in ids:
        if isinstance(i, str) and i and i not in seen:
            current.append(i)
            seen.add(i)
            added += 1
    return added


def _progress_section(sf):
    section = sf.progress.get("Progress")
    if not isinstance(section, dict):
        section = {}
        sf.progress["Progress"] = section
    return section


def _merge_section(sf, key, ids):
    progress = _progress_section(sf)
    current = progress.get(key)
    current = current if isinstance(current, list) else []
    added = merge_ids(current, ids)
    progress[key] = current
    return added, len(current)


def _owned_mount_refs(sf):
    character = sf.progress.get("Character")
    mount = character.get("Mount") if isinstance(character, dict) else None
    lst = mount.get("MountsUnlockedList") if isinstance(mount, dict) else None
    return set(lst) if isinstance(lst, list) else set()


def categories(sf):
    """Cards for the Unlocks page: [{key,label,have,total,done}]."""
    prog = sf.progress.get("Progress")
    prog = prog if isinstance(prog, dict) else {}

    def have(section, ids):
        cur = prog.get(section)
        return len(set(ids) & set(cur)) if isinstance(cur, list) else 0

    rows = [
        {"key": "recipes", "have": have("RecipesUnlocked", EMBEDDED_RECIPE_IDS),
         "total": len(set(EMBEDDED_RECIPE_IDS))},
        {"key": "buildings", "have": have("BuildingsUnlocked", EMBEDDED_BUILDING_IDS),
         "total": len(set(EMBEDDED_BUILDING_IDS))},
        {"key": "pickups", "have": have("ItemsPickedUp", EMBEDDED_ITEM_PICKUP_IDS),
         "total": len(set(EMBEDDED_ITEM_PICKUP_IDS))},
        {"key": "urns", "have": have("ShrinesUnlocked", EMBEDDED_SHRINE_IDS),
         "total": len(set(EMBEDDED_SHRINE_IDS))},
        {"key": "mounts",
         "have": len(set(ALL_MOUNT_REFS) & _owned_mount_refs(sf)),
         "total": len(ALL_MOUNT_REFS)},
    ]
    for r in rows:
        r["label"] = CATEGORY_LABELS[r["key"]]
        r["done"] = r["total"] > 0 and r["have"] >= r["total"]
    return rows


def unlock_all(sf, key):
    """Unlock every known entry in a category. Returns (added, total)."""
    if key == "recipes":
        added, total = _merge_section(sf, "RecipesUnlocked", EMBEDDED_RECIPE_IDS)
        _merge_section(sf, "RecipesNew", EMBEDDED_RECIPE_IDS)
    elif key == "buildings":
        added, total = _merge_section(sf, "BuildingsUnlocked", EMBEDDED_BUILDING_IDS)
        _merge_section(sf, "BuildingPiecesNew", EMBEDDED_BUILDING_IDS)
    elif key == "pickups":
        added, total = _merge_section(sf, "ItemsPickedUp", EMBEDDED_ITEM_PICKUP_IDS)
    elif key == "urns":
        added, total = _merge_section(sf, "ShrinesUnlocked", EMBEDDED_SHRINE_IDS)
    elif key == "mounts":
        return _unlock_all_mounts(sf)
    else:
        raise ValueError("Unknown unlock category: {}".format(key))
    sf.mark_dirty()
    return added, total


def _unlock_all_mounts(sf):
    character = sf.progress.get("Character")
    if not isinstance(character, dict):
        raise ValueError("Character data not found in this save.")
    mount = character.get("Mount")
    if not isinstance(mount, dict):
        mount = {}
        character["Mount"] = mount
    unlocked = mount.get("MountsUnlockedList")
    if not isinstance(unlocked, list):
        unlocked = []
    added = merge_ids(unlocked, ALL_MOUNT_REFS)
    mount["MountsUnlockedList"] = unlocked
    if not mount.get("MountEquipped") and DEFAULT_MOUNT:
        mount["MountEquipped"] = DEFAULT_MOUNT
    sf.mark_dirty()
    return added, len(unlocked)


def computed_max_hp(sf):
    """Max HP is derived, not stored: 100 + 10 per collected Sanguine Urn."""
    prog = sf.progress.get("Progress")
    shrines = prog.get("ShrinesUnlocked") if isinstance(prog, dict) else None
    count = len(shrines) if isinstance(shrines, list) else 0
    return BASE_MAX_HP + HP_PER_SHRINE * count


def reveal_map(sf):
    # save format 86 dropped RevealedRegionsDetectionActive; the game writes
    # only the bitmap now
    sf.progress["RevealedFog"] = {"RevealedRegionsBitmap": 4294967295}
    sf.mark_dirty()


def reset_status(sf):
    """Full heal: hunger/thirst/toxins/endurance/health/stamina back to
    fresh-character values, plus a full vital shield.

    This is a field-for-field port of tab_extra.py's reset_player_status:
    the write shapes below (e.g. SustenanceValue/SustenanceDecayBuffer, not
    a generic CurrentValue) match what that function actually wrote, since
    that behavior is the spec for this operation.
    """
    character = sf.progress.get("Character")
    if not isinstance(character, dict):
        raise ValueError("Character data not found in this save.")

    loadout = sf.progress.get("Loadout")
    if isinstance(loadout, dict):
        slot1 = loadout.get("1")
        if isinstance(slot1, dict):
            slot1["VitalShield"] = 75

    character["Sustenance"] = {"SustenanceValue": 100, "SustenanceDecayBuffer": 0}
    character["Hydration"] = {"HydrationValue": 100, "HydrationDecayBuffer": 0}
    character["Toxicity"] = {"ToxicityValue": 0, "HighestToxicityValue": 0}
    character["Endurance"] = {"EnduranceValue": 100, "EnduranceDecayBuffer": 0}
    character["Health"] = {"CurrentValue": 100}
    character["Stamina"] = {"CurrentValue": 100}
    character["SpecialCharge"] = {"CurrentValue": 100}

    sf.mark_dirty()
