"""Slot-container model shared by Inventory, Loadout and Storage.

Verified slot layout (from real saves — do not change):
Inventory: Bag 0-31 (0-7 action bar), Runes 32-55, Ammo 56-79, Quest 80-103.
Storage (PersonalInventory): 0-19.
"""
from collections import OrderedDict

from core.save_file import generate_guid, fix_max_slot_index
from data.item_maps import build_item_maps
from data.item_ids import ITEM_LIST

CONTAINERS = {
    "inventory": "Inventory",
    "loadout": "Loadout",
    "storage": "PersonalInventory",
}

INVENTORY_TABS = [
    ("Bag", 0, 31),
    ("Runes", 32, 55),
    ("Ammo", 56, 79),
    ("Quest", 80, 103),
]
STORAGE_RANGE = (0, 19)

_maps = None


def item_maps():
    """(id_to_name, name_to_id, id_to_guids, id_to_extra), built once."""
    global _maps
    if _maps is None:
        _maps = build_item_maps(ITEM_LIST)
    return _maps


def get_container(sf, name):
    key = CONTAINERS[name]
    root = sf.progress
    cur = root.get(key)
    if not isinstance(cur, OrderedDict):
        if isinstance(cur, dict):
            items = sorted(cur.items(),
                           key=lambda kv: int(kv[0]) if kv[0].isdigit() else 10 ** 6)
            root[key] = OrderedDict(items)
        else:
            root[key] = OrderedDict()
    return root[key]


def slots(sf, name):
    """{slot:int -> entry dict}; the MaxSlotIndex marker is excluded."""
    out = {}
    for k, v in get_container(sf, name).items():
        if isinstance(k, str) and k.isdigit() and isinstance(v, dict):
            out[int(k)] = v
    return out


def slot_bounds(name, tab=None):
    if name == "storage":
        return STORAGE_RANGE
    if tab is not None:
        for label, lo, hi in INVENTORY_TABS:
            if label == tab:
                return (lo, hi)
    return (0, 103)


def set_slot(sf, name, slot, item_id, count):
    lo, hi = slot_bounds(name)
    if not (lo <= slot <= hi):
        raise ValueError("Slot {} is out of range {}-{}.".format(slot, lo, hi))
    count = int(count)
    if count < 1:
        raise ValueError("Amount must be at least 1.")
    id_to_name, _, _, id_to_extra = item_maps()
    if item_id not in id_to_name:
        raise ValueError("Unknown item.")
    entry = {"GUID": generate_guid(), "ItemData": item_id, "Count": count}
    extra = id_to_extra.get(item_id) or {}
    if extra.get("Durability") is not None:
        entry["Durability"] = extra["Durability"]
    if extra.get("VitalShield") is not None:
        entry["VitalShield"] = extra["VitalShield"]
    container = get_container(sf, name)
    container[str(slot)] = entry
    fix_max_slot_index(container)
    sf.mark_dirty()


def clear_slot(sf, name, slot):
    container = get_container(sf, name)
    if str(slot) in container:
        del container[str(slot)]
        fix_max_slot_index(container)
        sf.mark_dirty()


def clear_container(sf, name):
    container = get_container(sf, name)
    for k in [k for k in container if k != "MaxSlotIndex"]:
        del container[k]
    fix_max_slot_index(container)
    if name == "inventory":
        # loadout entries that point at inventory slots would dangle
        loadout = get_container(sf, "loadout")
        refs = [k for k, v in list(loadout.items())
                if isinstance(v, dict) and "PlayerInventoryItemIndex" in v]
        for k in refs:
            del loadout[k]
        fix_max_slot_index(loadout)
    sf.mark_dirty()
