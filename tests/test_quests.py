import os

import pytest

from core.save_file import SaveFile
from core import inventory as inv, quests
from data.quest_data import EMBEDDED_QUESTS
from data.unlock_ids import EMBEDDED_RECIPE_IDS

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


# ---- embedded data integrity -------------------------------------------

def test_embedded_quests_complete_and_unique():
    assert len(EMBEDDED_QUESTS) == 58
    ids = [q["quest_id"] for q in EMBEDDED_QUESTS]
    assert len(set(ids)) == len(ids)
    assert all(q["name"] for q in EMBEDDED_QUESTS)
    assert all(q["category"] in ("main", "side", "tutorial")
               for q in EMBEDDED_QUESTS)


def test_reward_recipe_ids_are_strict_mode_safe():
    # RecipesUnlocked rejects unknown ids (strict mode) — every recipe
    # reward must come from the verified embedded recipe snapshot.
    reward_recipes = {r["item_id"] for q in EMBEDDED_QUESTS
                      for r in q["rewards"] if r["type"] == "recipe_unlock"}
    assert reward_recipes
    assert reward_recipes <= set(EMBEDDED_RECIPE_IDS)


def test_reward_item_ids_resolve_to_known_items():
    id_to_name, _, _, _ = inv.item_maps()
    reward_items = {r["item_id"] for q in EMBEDDED_QUESTS
                    for r in q["rewards"] if r["type"] == "item"}
    unknown = {i for i in reward_items if i and i not in id_to_name}
    assert not unknown, "unmapped reward items: {}".format(sorted(unknown))


# ---- state read/write ---------------------------------------------------

def test_set_state_creates_gamelike_entry():
    sf = _sf()
    qid = EMBEDDED_QUESTS[0]["quest_id"]
    quests.set_state(sf, qid, quests.STATE_COMPLETED)
    entry = [e for e in sf.progress["QuestProgress"]["Quests"]
             if e["QuestId"] == qid][0]
    # the game serializes no-objective as the FName string "None" — a JSON
    # null here makes the game drop the entry / corrupt the load
    assert entry == {"QuestId": qid, "QuestState": 2,
                     "QuestObjective": "None",
                     "QuestInts": [], "QuestBools": []}
    assert quests.get_states(sf)[qid] == quests.STATE_COMPLETED
    assert sf.dirty is True


def test_no_null_objective_is_ever_written():
    sf = _sf()
    whip = _quest("Quest_Whip")            # no objectives
    cooks = _quest("Quest_CooksAssistant")
    quests.set_state(sf, cooks["quest_id"], quests.STATE_IN_PROGRESS,
                     objective=None)       # explicit None
    quests.set_ready_to_turn_in(sf, whip)  # final_objective is None
    quests.set_state(sf, whip["quest_id"], quests.STATE_COMPLETED)
    quests.set_in_progress(sf, whip)       # objectiveless rewind
    quests.complete_all(sf, "side")
    for e in sf.progress["QuestProgress"]["Quests"]:
        assert isinstance(e["QuestObjective"], str), e


def test_get_objectives_reads_none_string_as_no_objective():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_state(sf, q["quest_id"], quests.STATE_IN_PROGRESS)
    assert quests.get_objectives(sf)[q["quest_id"]] is None


def test_set_state_updates_existing_entry_preserving_variables():
    sf = _sf()
    qid = "3MpWS0mD8A6yFVmjVAA2Qg"
    sf.progress["QuestProgress"] = {"Quests": [{
        "QuestId": qid, "QuestState": 1, "QuestObjective": "Objective1",
        "QuestInts": [{"QuestVariableName": "QuestBeat",
                       "QuestVariableValue": 3}],
        "QuestBools": [],
    }]}
    quests.set_state(sf, qid, quests.STATE_COMPLETED)
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestState"] == 2
    # quest variables and current objective are never touched
    assert entry["QuestObjective"] == "Objective1"
    assert entry["QuestInts"][0]["QuestVariableValue"] == 3


def test_complete_all_only_changes_incomplete():
    sf = _sf()
    main = quests.quests("main")
    quests.set_state(sf, main[0]["quest_id"], quests.STATE_COMPLETED)
    changed = quests.complete_all(sf, "main")
    assert changed == len(main) - 1
    states = quests.get_states(sf)
    assert all(states[q["quest_id"]] == 2 for q in main)
    assert quests.complete_all(sf, "main") == 0


# ---- reward granting ----------------------------------------------------

def _quest(asset):
    return [q for q in EMBEDDED_QUESTS if q["asset"] == asset][0]


def test_grant_item_rewards_fills_free_bag_slots():
    sf = _sf()
    q = _quest("Quest_FTUE_Q2")   # 3 rune stacks of 25
    before = dict(inv.slots(sf, "inventory"))
    granted, skipped = quests.grant_rewards(sf, q)
    assert len(granted) == 3 and not skipped
    after = inv.slots(sf, "inventory")
    new_slots = {s: e for s, e in after.items() if s not in before}
    assert len(new_slots) == 3
    lo, hi = inv.slot_bounds("inventory", "Bag")
    assert all(lo <= s <= hi for s in new_slots)
    assert sorted(e["Count"] for e in new_slots.values()) == [25, 25, 25]
    assert sf.dirty is True


def test_grant_recipe_reward_merges_unlocks():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    rid = q["rewards"][0]["item_id"]
    granted, skipped = quests.grant_rewards(sf, q)
    assert granted and not skipped
    prog = sf.progress["Progress"]
    assert rid in prog["RecipesUnlocked"]
    assert rid in prog["RecipesNew"]
    # second grant is a no-op skip, never a duplicate entry
    granted, skipped = quests.grant_rewards(sf, q)
    assert not granted and skipped
    assert prog["RecipesUnlocked"].count(rid) == 1


def test_grant_mount_reward_writes_bare_dataasset_ref():
    sf = _sf()
    sf.progress["Character"] = {}   # fixture is minimal; real saves have it
    q = _quest("Quest_FH_WitherBeast")
    granted, skipped = quests.grant_rewards(sf, q)
    assert granted and not skipped
    unlocked = sf.progress["Character"]["Mount"]["MountsUnlockedList"]
    ref = "MountDataAsset:DA_Mount_Terrorbird_00_00"
    assert ref in unlocked
    # strict rule: bare MountDataAsset: refs only, no type tags
    assert all(u.startswith("MountDataAsset:") for u in unlocked)
    quests.grant_rewards(sf, q)
    assert unlocked.count(ref) == 1


def test_grant_is_all_or_nothing_when_bag_is_short():
    sf = _sf()
    # leave only 2 free Bag slots; Quest_FTUE_Q2 has 3 item rewards
    lo, hi = inv.slot_bounds("inventory", "Bag")
    for s in range(lo, hi - 1):
        inv.set_slot(sf, "inventory", s, "lCE7i3iXGUuHv7FphIOcXg", 1)
    before = dict(inv.slots(sf, "inventory"))
    q = _quest("Quest_FTUE_Q2")
    granted, skipped = quests.grant_rewards(sf, q)
    assert not granted
    assert len(skipped) == 1
    assert "3 free Bag slots" in skipped[0] and "you have 2" in skipped[0]
    # nothing was placed anywhere — not even partially
    assert dict(inv.slots(sf, "inventory")) == before
    assert not inv.slots(sf, "storage")


# ---- ready to turn in ----------------------------------------------------

def test_set_ready_to_turn_in_uses_final_objective():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_ready_to_turn_in(sf, q)
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestState"] == quests.STATE_IN_PROGRESS
    assert entry["QuestObjective"] == q["objectives"][-1] == "Objective5"
    assert quests.display_state(
        q, entry["QuestState"], entry["QuestObjective"]) == quests.READY_LABEL


def test_display_state_distinguishes_ready_from_in_progress():
    q = _quest("Quest_CooksAssistant")
    assert quests.display_state(q, 1, "Objective1") == "In progress"
    assert quests.display_state(q, 1, None) == "In progress"
    assert quests.display_state(q, 2, "Objective5") == "Completed"
    assert quests.display_state(q, 0, None) == "Not started"


def test_ready_on_objectiveless_quest_is_plain_in_progress():
    sf = _sf()
    q = _quest("Quest_Whip")   # hidden quest with no objectives
    quests.set_ready_to_turn_in(sf, q)
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestState"] == quests.STATE_IN_PROGRESS
    assert entry["QuestObjective"] == "None"
    assert quests.display_state(q, 1, None) == "In progress"


def test_main_quests_listed_in_story_order():
    assert [q["asset"] for q in quests.quests("main")] == [
        "Quest_DragonSlayer", "Quest_DeathQuestMain",
        "Quest_DR_MainQuest", "Quest_UmS_MainQuest"]


def test_main_story_blockers_names_all_incomplete_predecessors():
    sf = _sf()
    last = _quest("Quest_UmS_MainQuest")
    assert quests.main_story_blockers(sf, last) == [
        "Dragon Slayer", "Withering Heights", "Black Knight's Fortress"]
    quests.set_state(sf, _quest("Quest_DragonSlayer")["quest_id"],
                     quests.STATE_COMPLETED)
    assert quests.main_story_blockers(sf, last) == [
        "Withering Heights", "Black Knight's Fortress"]


def test_main_story_blockers_empty_when_predecessors_complete():
    sf = _sf()
    for asset in ("Quest_DragonSlayer", "Quest_DeathQuestMain",
                  "Quest_DR_MainQuest"):
        quests.set_state(sf, _quest(asset)["quest_id"],
                         quests.STATE_COMPLETED)
    assert quests.main_story_blockers(sf, _quest("Quest_UmS_MainQuest")) == []
    # in-progress predecessor still blocks
    quests.set_state(sf, _quest("Quest_DR_MainQuest")["quest_id"],
                     quests.STATE_IN_PROGRESS)
    assert quests.main_story_blockers(
        sf, _quest("Quest_UmS_MainQuest")) == ["Black Knight's Fortress"]


def test_first_main_quest_and_side_quests_never_blocked():
    sf = _sf()
    assert quests.main_story_blockers(sf, _quest("Quest_DragonSlayer")) == []
    assert quests.main_story_blockers(sf, _quest("Quest_CooksAssistant")) == []


# ---- objective story order ------------------------------------------------

def test_objectives_follow_story_order_not_dump_order():
    # dump order lists the shard sub-steps AFTER the ending; the numeric
    # ids encode the real ladder (verified: real completed save ends at
    # _6, wiki walkthrough has Speak To Death as the intro step)
    o = _quest("Quest_DR_MainQuest")["objectives"]
    assert o[0] == "DR_Main_Objective_-1"          # Speak To Death intro
    assert o[-1] == "DR_Main_Objective_6"          # completes at the stone
    assert o.index("DR_Main_Objective_4_13") < o.index("DR_Main_Objective_5")
    assert o.index("DR_Main_Objective_4_-1") == \
        o.index("DR_Main_Objective_4") + 1
    assert quests.final_objective(_quest("Quest_DR_MainQuest")) == \
        "DR_Main_Objective_6"


def test_ums_main_quest_objectives_follow_wiki_story_order():
    # text ids, so the order is pinned by hand (wiki walkthrough): the
    # dump listed 'Enter the Umbral Sands' 17th of 18 and ended on
    # FindLastKey instead of the Fuzan's-head turn-in
    ums = _quest("Quest_UmS_MainQuest")
    o = ums["objectives"]
    assert o[0] == "EnterUmS"
    assert o[-1] == "ReturnToIcthlarin"
    assert quests.final_objective(ums) == "ReturnToIcthlarin"
    assert o.index("SpeakToIcthlarin") < o.index(
        "FirstGarouEarnReputation.NoReputation")
    assert o.index("FirstGarouEarnReputation.MaxReputation") \
        < o.index("FindThreeKeys") < o.index("FindLastKey") \
        < o.index("RepairTheMirrors") < o.index("SlayFuzan")


def test_story_order_overrides_match_dumped_objectives():
    # a game update that changes a pinned quest must fail the build
    # (the override silently falls back to dump order at runtime)
    for asset, pinned in quests._STORY_ORDER_OVERRIDES.items():
        assert sorted(pinned) == sorted(_quest(asset)["objectives"]), asset


def test_text_id_objectives_keep_dump_order():
    slayer = _quest("Quest_DragonSlayer")["objectives"]
    assert slayer[0] == "Claim a bed"
    assert slayer[-1] == "Return to the Wise old man after killing velgar"
    assert _quest("Quest_DeathQuestMain")["objectives"][-1] == "ReturnToDeath"
    cooks = _quest("Quest_CooksAssistant")["objectives"]
    assert cooks[0] == "Objective1" and cooks[-1] == "Objective5"


# ---- objective ladder -----------------------------------------------------

def test_set_objective_puts_quest_in_progress_at_that_objective():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_objective(sf, q, q["objectives"][2])
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestState"] == quests.STATE_IN_PROGRESS
    assert entry["QuestObjective"] == q["objectives"][2]
    assert sf.dirty is True


def test_set_objective_rejects_unknown_id():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    with pytest.raises(ValueError):
        quests.set_objective(sf, q, "NotARealObjective")
    assert quests.get_states(sf) == {}


def test_set_objective_at_final_objective_reads_ready_to_turn_in():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_objective(sf, q, q["objectives"][-1])
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert quests.display_state(
        q, entry["QuestState"], entry["QuestObjective"]) == quests.READY_LABEL


def test_objective_label_uses_text_with_id_fallback():
    dr = _quest("Quest_DR_MainQuest")
    assert quests.objective_label(dr, "DR_Main_Objective_2") == \
        "Speak to Doric in Dowdun Reach"
    # ids without a text entry fall back to the id itself
    assert quests.objective_label(dr, "Some_Unknown_Id") == "Some_Unknown_Id"


# ---- uncompleting ---------------------------------------------------------

def test_reset_quest_removes_the_save_entry():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_state(sf, q["quest_id"], quests.STATE_COMPLETED)
    assert quests.reset_quest(sf, q["quest_id"]) is True
    assert sf.progress["QuestProgress"]["Quests"] == []
    assert quests.get_states(sf) == {}


def test_reset_quest_without_entry_is_a_noop():
    sf = _sf()
    assert quests.reset_quest(sf, "no-such-quest") is False


def test_set_in_progress_from_completed_rewinds_to_first_objective():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_state(sf, q["quest_id"], quests.STATE_COMPLETED,
                     objective=q["objectives"][-1])
    quests.set_in_progress(sf, q)
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestState"] == quests.STATE_IN_PROGRESS
    assert entry["QuestObjective"] == q["objectives"][0]


def test_set_in_progress_otherwise_keeps_the_current_objective():
    sf = _sf()
    q = _quest("Quest_CooksAssistant")
    quests.set_objective(sf, q, q["objectives"][2])
    quests.set_in_progress(sf, q)
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestObjective"] == q["objectives"][2]


def test_set_in_progress_from_completed_objectiveless_quest():
    sf = _sf()
    q = _quest("Quest_Whip")   # hidden quest with no objectives
    quests.set_state(sf, q["quest_id"], quests.STATE_COMPLETED)
    quests.set_in_progress(sf, q)
    entry = sf.progress["QuestProgress"]["Quests"][0]
    assert entry["QuestState"] == quests.STATE_IN_PROGRESS
    assert entry["QuestObjective"] == "None"


def test_uncomplete_blockers_name_later_completed_main_quests_in_order():
    sf = _sf()
    for asset in ("Quest_DragonSlayer", "Quest_DeathQuestMain",
                  "Quest_DR_MainQuest", "Quest_UmS_MainQuest"):
        quests.set_state(sf, _quest(asset)["quest_id"],
                         quests.STATE_COMPLETED)
    assert quests.main_story_uncomplete_blockers(
        sf, _quest("Quest_DeathQuestMain")) == [
        "Black Knight's Fortress", "Icthlarin's Little Helper"]
    assert quests.main_story_uncomplete_blockers(
        sf, _quest("Quest_UmS_MainQuest")) == []


def test_rewind_removes_later_non_completed_main_quest_entries():
    sf = _sf()
    quests.set_state(sf, _quest("Quest_DragonSlayer")["quest_id"],
                     quests.STATE_COMPLETED)
    quests.set_state(sf, _quest("Quest_DeathQuestMain")["quest_id"],
                     quests.STATE_IN_PROGRESS)
    quests.set_objective(sf, _quest("Quest_DR_MainQuest"),
                         _quest("Quest_DR_MainQuest")["objectives"][0])
    # rewinding the story to Dragon Slayer resets both later active quests
    names = quests.rewind_later_main_quests(sf, _quest("Quest_DragonSlayer"))
    assert names == ["Withering Heights", "Black Knight's Fortress"]
    states = quests.get_states(sf)
    assert _quest("Quest_DeathQuestMain")["quest_id"] not in states
    assert _quest("Quest_DR_MainQuest")["quest_id"] not in states


def test_rewind_keeps_later_completed_main_quests_and_non_main():
    sf = _sf()
    quests.set_state(sf, _quest("Quest_UmS_MainQuest")["quest_id"],
                     quests.STATE_COMPLETED)
    quests.set_state(sf, _quest("Quest_CooksAssistant")["quest_id"],
                     quests.STATE_IN_PROGRESS)
    assert quests.rewind_later_main_quests(
        sf, _quest("Quest_DragonSlayer")) == []
    states = quests.get_states(sf)
    assert states[_quest("Quest_UmS_MainQuest")["quest_id"]] == 2
    assert states[_quest("Quest_CooksAssistant")["quest_id"]] == 1
    assert quests.rewind_later_main_quests(
        sf, _quest("Quest_CooksAssistant")) == []


def test_uncomplete_blockers_ignore_non_completed_and_non_main():
    sf = _sf()
    quests.set_state(sf, _quest("Quest_UmS_MainQuest")["quest_id"],
                     quests.STATE_IN_PROGRESS)
    assert quests.main_story_uncomplete_blockers(
        sf, _quest("Quest_DragonSlayer")) == []
    assert quests.main_story_uncomplete_blockers(
        sf, _quest("Quest_CooksAssistant")) == []


# ---- Umbral Sands camp sync ------------------------------------------------
# the UmS objective is derived by the game from favour ints / task bools on
# the main quest entry plus the nine parallel tribe task quests — jumping
# the ladder must write all of it, not just the objective FName

def _ums():
    return _quest("Quest_UmS_MainQuest")


def _ums_task(tribe, n):
    return _quest("Quest_UmS_MainQuest1_Tribe{}_Task{}".format(tribe, n))


def _entry_of(sf, quest_id):
    return [e for e in sf.progress["QuestProgress"]["Quests"]
            if e["QuestId"] == quest_id][0]


def _ints(entry):
    return {i["QuestVariableName"]: i["QuestVariableValue"]
            for i in entry["QuestInts"]}


def _bools(entry):
    return {b["QuestVariableName"]: b["QuestVariableValue"]
            for b in entry["QuestBools"]}


def test_every_pinned_ums_objective_has_a_variable_profile():
    for oid in quests._STORY_ORDER_OVERRIDES["Quest_UmS_MainQuest"]:
        assert oid in quests._UMS_PROFILES, oid


def test_jump_to_no_reputation_accepts_all_alcarrid_tasks_together():
    sf = _sf()
    notes = quests.set_objective(
        sf, _ums(), "FirstGarouEarnReputation.NoReputation")
    assert notes   # the sync tells the user what moved
    e = _entry_of(sf, _ums()["quest_id"])
    ints, bools = _ints(e), _bools(e)
    assert ints["DT_QuestBeat"] == 3
    assert ints["FirstCampFavour"] == 0
    assert bools["TribeA.SpokenToElder"] and bools["HideStartNPC"]
    # the elder hands out all three tasks at once (matches a real save)
    assert bools["TribeA.Taskgiver1.TaskGiven"]
    assert bools["TribeA.Taskgiver2.SpokenTo"]
    assert bools["TribeA.Taskgiver3.SpokenTo"]
    states = quests.get_states(sf)
    objectives = quests.get_objectives(sf)
    for n in (1, 2, 3):
        t = _ums_task("A", n)
        assert states[t["quest_id"]] == quests.STATE_IN_PROGRESS
        assert objectives[t["quest_id"]] == t["objectives"][0]
    # the other camps are untouched
    assert _ums_task("B", 1)["quest_id"] not in states
    assert "TribeBFavour" not in ints
    assert "TribeA.Task1.HandedIn" not in bools


def test_jump_to_max_reputation_completes_the_alcarrid_camp():
    sf = _sf()
    quests.set_objective(sf, _ums(),
                         "FirstGarouEarnReputation.MaxReputation")
    e = _entry_of(sf, _ums()["quest_id"])
    ints, bools = _ints(e), _bools(e)
    assert ints["FirstCampFavour"] == 100
    assert ints["Task1FavourGained"] == 25
    assert bools["FirstCampMaxFavourEarned"]
    assert bools["TribeA.Task1.HandedIn"] and bools["TribeA.Task2Complete"]
    states = quests.get_states(sf)
    for n in (1, 2, 3):
        assert states[_ums_task("A", n)["quest_id"]] == \
            quests.STATE_COMPLETED


def test_jump_to_find_three_keys_opens_both_remaining_camps():
    sf = _sf()
    quests.set_objective(sf, _ums(), "FindThreeKeys")
    e = _entry_of(sf, _ums()["quest_id"])
    ints, bools = _ints(e), _bools(e)
    assert ints["DT_QuestBeat"] == 4 and ints["KeysFound"] == 0
    assert ints["TribeBFavour"] == 0 and ints["TribeCFavour"] == 0
    assert bools["FinishedCampA"]
    assert bools["SpokenToTribeBElder"] and bools["SpokenToTribeCElder"]
    states = quests.get_states(sf)
    for tribe in ("B", "C"):
        for n in (1, 2, 3):
            assert states[_ums_task(tribe, n)["quest_id"]] == \
                quests.STATE_IN_PROGRESS


def test_jump_backward_rewinds_favour_tasks_and_bools():
    sf = _sf()
    quests.set_objective(sf, _ums(), "FindThreeKeys")
    quests.set_objective(sf, _ums(),
                         "FirstGarouEarnReputation.NoReputation")
    e = _entry_of(sf, _ums()["quest_id"])
    ints, bools = _ints(e), _bools(e)
    assert ints["FirstCampFavour"] == 0 and ints["DT_QuestBeat"] == 3
    # camp B/C state is unset again, exactly like a save that never got there
    assert "TribeBFavour" not in ints and "KeysFound" not in ints
    assert "FinishedCampA" not in bools
    states = quests.get_states(sf)
    for n in (1, 2, 3):   # completed A tasks downgrade to freshly accepted
        assert states[_ums_task("A", n)["quest_id"]] == \
            quests.STATE_IN_PROGRESS
    for tribe in ("B", "C"):
        for n in (1, 2, 3):
            assert _ums_task(tribe, n)["quest_id"] not in states


def test_completing_the_main_quest_applies_the_full_profile():
    sf = _sf()
    quests.set_state(sf, _ums()["quest_id"], quests.STATE_COMPLETED)
    e = _entry_of(sf, _ums()["quest_id"])
    ints = _ints(e)
    assert ints["DT_QuestBeat"] == 6 and ints["MirrorsRepaired"] == 3
    assert ints["KeysFound"] == 2
    states = quests.get_states(sf)
    for tribe in ("A", "B", "C"):
        for n in (1, 2, 3):
            assert states[_ums_task(tribe, n)["quest_id"]] == \
                quests.STATE_COMPLETED


def test_completing_a_tribe_task_feeds_favour_and_moves_the_rung():
    sf = _sf()
    quests.set_objective(sf, _ums(),
                         "FirstGarouEarnReputation.NoReputation")
    notes = quests.set_state(sf, _ums_task("A", 1)["quest_id"],
                             quests.STATE_COMPLETED)
    assert notes
    e = _entry_of(sf, _ums()["quest_id"])
    assert _ints(e)["FirstCampFavour"] == 25
    assert _bools(e)["TribeA.Task1.HandedIn"]
    assert e["QuestObjective"] == "FirstGarouEarnReputation.LowReputation"
    # tasks 1+2+3 = 25+25+50 favour: completing all reaches Max directly
    quests.set_state(sf, _ums_task("A", 2)["quest_id"],
                     quests.STATE_COMPLETED)
    quests.set_state(sf, _ums_task("A", 3)["quest_id"],
                     quests.STATE_COMPLETED)
    e = _entry_of(sf, _ums()["quest_id"])
    assert _ints(e)["FirstCampFavour"] == 100
    assert _bools(e)["FirstCampMaxFavourEarned"]
    assert e["QuestObjective"] == "FirstGarouEarnReputation.MaxReputation"


def test_uncompleting_a_tribe_task_lowers_favour_and_the_rung():
    sf = _sf()
    quests.set_objective(sf, _ums(),
                         "FirstGarouEarnReputation.MaxReputation")
    quests.set_in_progress(sf, _ums_task("A", 3))
    e = _entry_of(sf, _ums()["quest_id"])
    assert _ints(e)["FirstCampFavour"] == 50
    assert "TribeA.Task3.Complete" not in _bools(e)
    assert "FirstCampMaxFavourEarned" not in _bools(e)
    assert e["QuestObjective"] == \
        "FirstGarouEarnReputation.MediumReputation"


def test_tribe_task_edits_without_the_main_quest_do_not_invent_it():
    sf = _sf()
    assert quests.set_state(sf, _ums_task("B", 2)["quest_id"],
                            quests.STATE_COMPLETED) == []
    assert _ums()["quest_id"] not in quests.get_states(sf)


def test_resetting_the_main_quest_resets_the_tribe_tasks():
    sf = _sf()
    quests.set_objective(sf, _ums(), "FindThreeKeys")
    assert quests.reset_quest(sf, _ums()["quest_id"]) is True
    states = quests.get_states(sf)
    for tribe in ("A", "B", "C"):
        for n in (1, 2, 3):
            assert _ums_task(tribe, n)["quest_id"] not in states


def test_reputation_rung_labels_are_disambiguated():
    ums = _ums()
    low = quests.objective_label(ums,
                                 "FirstGarouEarnReputation.LowReputation")
    high = quests.objective_label(ums,
                                  "FirstGarouEarnReputation.HighReputation")
    assert low != high
    assert low.endswith("(Low Reputation)")
