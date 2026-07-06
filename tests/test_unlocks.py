import os

import pytest

from core.save_file import SaveFile
from core import unlocks
from data.unlock_ids import EMBEDDED_RECIPE_IDS, EMBEDDED_MOUNT_TAGS
from data.shrine_ids import EMBEDDED_SHRINE_IDS

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


def test_merge_ids_union_only():
    current = ["b", "a"]
    added = unlocks.merge_ids(current, ["a", "c", "c", 5, None])
    assert added == 1                      # only "c" is new and valid
    assert current == ["b", "a", "c"]      # order of existing preserved


def test_mount_refs_are_bare_dataasset_refs():
    # Strict rule: MountsUnlockedList only accepts MountDataAsset: refs
    assert unlocks.ALL_MOUNT_REFS
    assert all(r.startswith("MountDataAsset:") for r in unlocks.ALL_MOUNT_REFS)
    assert len(unlocks.ALL_MOUNT_REFS) <= len(EMBEDDED_MOUNT_TAGS)


def test_unlock_all_recipes_sets_both_lists():
    sf = _sf()
    added, total = unlocks.unlock_all(sf, "recipes")
    assert total == len(set(EMBEDDED_RECIPE_IDS))
    prog = sf.progress["Progress"]
    assert set(prog["RecipesUnlocked"]) >= set(EMBEDDED_RECIPE_IDS)
    assert set(prog["RecipesNew"]) >= set(EMBEDDED_RECIPE_IDS)
    assert sf.dirty is True


def test_unlock_all_is_idempotent_and_preserves_existing():
    sf = _sf()
    sf.progress.setdefault("Progress", {})["RecipesUnlocked"] = ["custom-id"]
    unlocks.unlock_all(sf, "recipes")
    added, total = unlocks.unlock_all(sf, "recipes")
    assert added == 0
    assert "custom-id" in sf.progress["Progress"]["RecipesUnlocked"]


def test_unlock_mounts_writes_list_and_equips_default():
    sf = _sf()
    sf.progress.setdefault("Character", {})
    added, total = unlocks.unlock_all(sf, "mounts")
    mount = sf.progress["Character"]["Mount"]
    assert set(mount["MountsUnlockedList"]) == set(unlocks.ALL_MOUNT_REFS)
    assert mount["MountEquipped"] in unlocks.ALL_MOUNT_REFS


def test_unlock_mounts_without_character_raises():
    sf = _sf()
    sf.progress.pop("Character", None)
    with pytest.raises(ValueError):
        unlocks.unlock_all(sf, "mounts")


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        unlocks.unlock_all(_sf(), "nope")


def test_categories_counts():
    sf = _sf()
    rows = {r["key"]: r for r in unlocks.categories(sf)}
    assert set(rows) == {"recipes", "buildings", "pickups", "urns", "mounts"}
    assert rows["urns"]["total"] == len(EMBEDDED_SHRINE_IDS)
    assert rows["recipes"]["done"] is False
    unlocks.unlock_all(sf, "recipes")
    rows = {r["key"]: r for r in unlocks.categories(sf)}
    assert rows["recipes"]["done"] is True
    assert rows["recipes"]["have"] == rows["recipes"]["total"]


def test_computed_max_hp():
    sf = _sf()
    sf.progress.setdefault("Progress", {})["ShrinesUnlocked"] = []
    assert unlocks.computed_max_hp(sf) == 100
    unlocks.unlock_all(sf, "urns")
    assert unlocks.computed_max_hp(sf) == 100 + 10 * len(EMBEDDED_SHRINE_IDS)


def test_reveal_map():
    sf = _sf()
    unlocks.reveal_map(sf)
    fog = sf.progress["RevealedFog"]
    assert fog["RevealedRegionsBitmap"] == 4294967295
    assert fog["RevealedRegionsDetectionActive"] is True
    assert sf.dirty is True


def test_reset_status():
    # Field-for-field port of tab_extra.py's reset_player_status: the field
    # names below (SustenanceValue/HydrationValue/ToxicityValue/...) are the
    # actual save-file keys the old code wrote, NOT a generic "CurrentValue"
    # shape. Health and Stamina are the two vitals that really do use
    # CurrentValue.
    sf = _sf()
    sf.progress.setdefault("Character", {})
    unlocks.reset_status(sf)
    ch = sf.progress["Character"]
    assert ch["Health"]["CurrentValue"] == 100
    assert ch["Stamina"]["CurrentValue"] == 100
    assert ch["Sustenance"] == {"SustenanceValue": 100, "SustenanceDecayBuffer": 0}
    assert ch["Hydration"] == {"HydrationValue": 100, "HydrationDecayBuffer": 0}
    assert ch["Toxicity"] == {"ToxicityValue": 0, "HighestToxicityValue": 0}
    assert ch["Endurance"] == {"EnduranceValue": 100, "EnduranceDecayBuffer": 0}
    assert sf.dirty is True


def test_reset_status_updates_existing_loadout_slot_only():
    # Old behavior: VitalShield is only written when Loadout["1"] already
    # exists as a dict; reset_status must not create it.
    sf = _sf()
    sf.progress.setdefault("Character", {})
    sf.progress["Loadout"] = {"1": {"Foo": "bar"}}
    unlocks.reset_status(sf)
    assert sf.progress["Loadout"]["1"]["VitalShield"] == 75

    sf2 = _sf()
    sf2.progress.setdefault("Character", {})
    unlocks.reset_status(sf2)
    assert "Loadout" not in sf2.progress


def test_reset_status_without_character_raises():
    sf = _sf()
    sf.progress.pop("Character", None)
    with pytest.raises(ValueError):
        unlocks.reset_status(sf)
