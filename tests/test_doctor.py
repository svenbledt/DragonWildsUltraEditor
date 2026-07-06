import os

from core.save_file import SaveFile
from core import doctor
from data.doctor_ids import BAD_PICKUP_IDS, BAD_RECIPE_IDS

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

FIRE_CAPE_VESTIGE = "NndX3U-UM-JVFaKvgrz8Eg"


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


def test_blocklists_are_populated_and_disjoint_from_good_sets():
    from data.pickup_ids import EMBEDDED_ITEM_PICKUP_IDS
    from data.unlock_ids import EMBEDDED_RECIPE_IDS
    assert FIRE_CAPE_VESTIGE in BAD_PICKUP_IDS
    assert not set(BAD_PICKUP_IDS) & set(EMBEDDED_ITEM_PICKUP_IDS)
    assert not set(BAD_RECIPE_IDS) & set(EMBEDDED_RECIPE_IDS)


def test_healthy_save_scans_clean_and_fix_all_is_noop():
    sf = _sf()
    sf.progress["Progress"] = {
        "ItemsPickedUp": ["lWGe1hSwiECAS9xhsMzJfg"],
        "RecipesUnlocked": ["-182uUqijEQbDqeWGlTOQw"],
    }
    assert doctor.scan(sf) == []
    assert doctor.fix_all(sf) == 0
    assert sf.progress["Progress"]["ItemsPickedUp"] == [
        "lWGe1hSwiECAS9xhsMzJfg"]


def test_fire_cape_vestige_detected_and_removed():
    sf = _sf()
    good = "lWGe1hSwiECAS9xhsMzJfg"
    sf.progress["Progress"] = {"ItemsPickedUp": [good, FIRE_CAPE_VESTIGE]}
    report = doctor.scan(sf)
    assert [r["key"] for r in report] == ["bad_ids"]
    assert "ItemsPickedUp" in report[0]["details"][0]
    assert doctor.fix(sf, "bad_ids") == 1
    assert sf.progress["Progress"]["ItemsPickedUp"] == [good]
    assert sf.dirty is True
    assert doctor.scan(sf) == []


def test_bad_recipe_ids_removed_from_both_lists():
    sf = _sf()
    bad = BAD_RECIPE_IDS[0]
    good = "-182uUqijEQbDqeWGlTOQw"
    sf.progress["Progress"] = {"RecipesUnlocked": [bad, good],
                               "RecipesNew": [bad]}
    assert doctor.fix(sf, "bad_ids") == 2
    assert sf.progress["Progress"]["RecipesUnlocked"] == [good]
    assert sf.progress["Progress"]["RecipesNew"] == []


def test_invalid_mount_refs_removed_valid_kept():
    sf = _sf()
    valid = "MountDataAsset:DA_Mount_Terrorbird_00_00"
    sf.progress["Character"] = {"Mount": {"MountsUnlockedList": [
        valid,
        "MountType:DA_Mount_Terrorbird_00_00",   # type tag corrupts save
        "MountDataAsset:DA_Mount_DevTest",       # unknown ref
    ]}}
    report = doctor.scan(sf)
    assert any(r["key"] == "mounts" for r in report)
    assert doctor.fix(sf, "mounts") == 2
    assert sf.progress["Character"]["Mount"]["MountsUnlockedList"] == [valid]


def test_duplicates_deduped_preserving_first_seen_order():
    sf = _sf()
    sf.progress["Progress"] = {
        "ItemsPickedUp": ["a", "b", "a", "c", "b"],
        "ShrinesUnlocked": ["s1", "s1"],
    }
    report = doctor.scan(sf)
    assert any(r["key"] == "duplicates" for r in report)
    assert doctor.fix(sf, "duplicates") == 3
    assert sf.progress["Progress"]["ItemsPickedUp"] == ["a", "b", "c"]
    assert sf.progress["Progress"]["ShrinesUnlocked"] == ["s1"]


def test_fix_all_repairs_everything_in_one_pass():
    sf = _sf()
    sf.progress["Progress"] = {
        "ItemsPickedUp": [FIRE_CAPE_VESTIGE, "good", "good"],
    }
    sf.progress["Character"] = {"Mount": {"MountsUnlockedList": ["junk"]}}
    assert doctor.fix_all(sf) == 3
    assert doctor.scan(sf) == []
    assert sf.progress["Progress"]["ItemsPickedUp"] == ["good"]


def test_null_quest_objectives_detected_and_repaired():
    sf = _sf()
    sf.progress["QuestProgress"] = {"Quests": [
        {"QuestId": "a", "QuestState": 2, "QuestObjective": None,
         "QuestInts": [], "QuestBools": []},
        {"QuestId": "b", "QuestState": 1, "QuestObjective": "Objective1",
         "QuestInts": [], "QuestBools": []},
        {"QuestId": "c", "QuestState": 0, "QuestObjective": "None",
         "QuestInts": [], "QuestBools": []},
    ]}
    report = doctor.scan(sf)
    assert [r["key"] for r in report] == ["quest_objectives"]
    assert doctor.fix(sf, "quest_objectives") == 1
    entries = sf.progress["QuestProgress"]["Quests"]
    # repaired to the FName string the game itself writes, others untouched
    assert entries[0]["QuestObjective"] == "None"
    assert entries[1]["QuestObjective"] == "Objective1"
    assert sf.dirty is True
    assert doctor.scan(sf) == []
