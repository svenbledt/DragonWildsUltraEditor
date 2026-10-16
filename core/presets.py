"""Apply region+class gear/storage templates to a save.

Templates live in data/loadout_presets.py, keyed by preset_key(region, cls).
Gear apply replaces Inventory+Loadout but preserves any existing Runes /
Ammo / Quest slots the template doesn't fill (players keep their runes).
"""
from data.loadout_presets import (
    GEAR_LOADOUTS, STORAGE_PRESETS, REGIONS, CLASSES, preset_key,
    RUNE_TAB, AMMO_TAB, QUEST_TAB,
)
from core.save_file import guidify_dict, fix_max_slot_index

# Protected tabs: Runes, Ammo, Quest (same ranges as core/inventory.py
# INVENTORY_TABS and the templates in data/loadout_presets.py).
_PROTECTED = [RUNE_TAB, AMMO_TAB, QUEST_TAB]


def _is_protected(slot):
    return any(lo <= slot <= hi for lo, hi in _PROTECTED)


def apply_gear_preset(sf, region, cls):
    key = preset_key(region, cls)
    gear = GEAR_LOADOUTS.get(key)
    if not gear:
        raise ValueError("No gear kit for {} / {}.".format(region, cls))
    new_inv = guidify_dict(gear["Inventory"])
    old_inv = sf.progress.get("Inventory")
    if isinstance(old_inv, dict):
        for k, v in old_inv.items():
            if isinstance(k, str) and k.isdigit() and _is_protected(int(k)) \
                    and k not in new_inv:
                new_inv[k] = v
    sf.progress["Inventory"] = new_inv
    sf.progress["Loadout"] = guidify_dict(gear["Loadout"])
    fix_max_slot_index(sf.progress["Inventory"])
    fix_max_slot_index(sf.progress["Loadout"])
    sf.mark_dirty()
    return key


def apply_storage_preset(sf, region, cls):
    key = preset_key(region, cls)
    preset = STORAGE_PRESETS.get(key)
    if not preset or "PersonalInventory" not in preset:
        raise ValueError("No storage kit for {} / {}.".format(region, cls))
    sf.progress["PersonalInventory"] = guidify_dict(preset["PersonalInventory"])
    fix_max_slot_index(sf.progress["PersonalInventory"])
    sf.mark_dirty()
    return key
