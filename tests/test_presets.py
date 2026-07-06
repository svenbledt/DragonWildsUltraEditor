import os

import pytest

from core.save_file import SaveFile
from core import presets, inventory as inv
from data.loadout_presets import GEAR_LOADOUTS, STORAGE_PRESETS, preset_key

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


def _region_class_for(key):
    for region in presets.REGIONS:
        for cls in presets.CLASSES:
            if preset_key(region, cls) == key:
                return region, cls
    raise AssertionError("no region/class combo for " + key)


def test_apply_gear_preset_fills_containers():
    sf = _sf()
    key = next(iter(GEAR_LOADOUTS))
    region, cls = _region_class_for(key)
    assert presets.apply_gear_preset(sf, region, cls) == key
    assert sf.dirty is True
    inv_slots = inv.slots(sf, "inventory")
    assert inv_slots, "gear preset should place inventory items"
    assert all("GUID" in e or "PlayerInventoryItemIndex" in e
               for e in inv_slots.values())
    container = inv.get_container(sf, "inventory")
    assert list(container.keys())[-1] == "MaxSlotIndex"


def test_apply_gear_preset_preserves_protected_slots():
    sf = _sf()
    key = next(iter(GEAR_LOADOUTS))
    region, cls = _region_class_for(key)
    gear_inv = GEAR_LOADOUTS[key]["Inventory"]
    # a rune-tab slot the template does NOT fill must survive the apply
    free = next(s for s in range(32, 56) if str(s) not in gear_inv)
    sentinel = {"GUID": "K" * 22, "ItemData": "keep-me", "Count": 7}
    inv.get_container(sf, "inventory")[str(free)] = dict(sentinel)
    presets.apply_gear_preset(sf, region, cls)
    kept = inv.slots(sf, "inventory")[free]
    assert kept["ItemData"] == "keep-me" and kept["Count"] == 7


def test_apply_gear_preset_unknown_combo_raises():
    with pytest.raises(ValueError):
        presets.apply_gear_preset(_sf(), "Nowhere", "Nobody")


def test_apply_storage_preset():
    sf = _sf()
    key = next(iter(STORAGE_PRESETS))
    region, cls = _region_class_for(key)
    assert presets.apply_storage_preset(sf, region, cls) == key
    slots = inv.slots(sf, "storage")
    assert slots
    assert all(0 <= s <= 20 for s in slots)
