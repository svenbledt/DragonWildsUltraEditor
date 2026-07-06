import os
from collections import OrderedDict

import pytest

from core.save_file import SaveFile
from core import inventory as inv

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


def _any_item_id():
    id_to_name, _, _, _ = inv.item_maps()
    return next(iter(id_to_name))


def test_tabs_and_ranges():
    assert inv.INVENTORY_TABS == [
        ("Bag", 0, 31), ("Runes", 32, 55), ("Ammo", 56, 79), ("Quest", 80, 103),
    ]
    assert inv.STORAGE_RANGE == (0, 19)
    assert inv.slot_bounds("storage") == (0, 19)
    assert inv.slot_bounds("inventory", "Runes") == (32, 55)
    assert inv.slot_bounds("inventory") == (0, 103)


def test_item_maps_memoized_and_populated():
    a = inv.item_maps()
    b = inv.item_maps()
    assert a is b
    id_to_name, name_to_id, _, _ = a
    assert len(id_to_name) > 100
    assert len(name_to_id) == len(id_to_name)  # names disambiguated


def test_get_container_creates_ordereddict():
    sf = _sf()
    c = inv.get_container(sf, "storage")
    assert isinstance(c, OrderedDict)
    assert sf.progress["PersonalInventory"] is c


def test_set_slot_writes_entry_and_marker():
    sf = _sf()
    iid = _any_item_id()
    inv.set_slot(sf, "storage", 3, iid, 5)
    c = inv.get_container(sf, "storage")
    entry = c["3"]
    assert entry["ItemData"] == iid and entry["Count"] == 5
    assert len(entry["GUID"]) == 22
    assert list(c.keys())[-1] == "MaxSlotIndex" and c["MaxSlotIndex"] == 3
    assert sf.dirty is True
    assert inv.slots(sf, "storage")[3] is entry


def test_set_slot_validates():
    sf = _sf()
    iid = _any_item_id()
    with pytest.raises(ValueError):
        inv.set_slot(sf, "storage", 20, iid, 1)      # out of storage range
    with pytest.raises(ValueError):
        inv.set_slot(sf, "inventory", 104, iid, 1)   # out of inventory range
    with pytest.raises(ValueError):
        inv.set_slot(sf, "storage", 0, iid, 0)       # bad amount
    with pytest.raises(ValueError):
        inv.set_slot(sf, "storage", 0, "not-a-real-id", 1)


def test_clear_slot():
    sf = _sf()
    iid = _any_item_id()
    inv.set_slot(sf, "storage", 2, iid, 1)
    inv.clear_slot(sf, "storage", 2)
    assert 2 not in inv.slots(sf, "storage")
    assert inv.get_container(sf, "storage")["MaxSlotIndex"] == -1


def test_clear_inventory_drops_dangling_loadout_refs():
    sf = _sf()
    iid = _any_item_id()
    inv.set_slot(sf, "inventory", 0, iid, 1)
    loadout = inv.get_container(sf, "loadout")
    loadout["1"] = {"PlayerInventoryItemIndex": 0}
    loadout["2"] = {"ItemData": iid, "Count": 1, "GUID": "x" * 22}
    inv.clear_container(sf, "inventory")
    assert inv.slots(sf, "inventory") == {}
    remaining = inv.slots(sf, "loadout")
    assert 1 not in remaining          # ref to cleared inventory dropped
    assert 2 in remaining              # direct entry kept
