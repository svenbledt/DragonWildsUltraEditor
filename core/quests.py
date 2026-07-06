"""Quest progress operations on GameProgress.QuestProgress.

Save layout (verified against real saves + game files):
Quests[] entries: {QuestId, QuestState, QuestObjective, QuestInts, QuestBools}.
QuestState is EQuestState: 0=Ungiven, 1=Given, 2=Complete. A quest with no
entry is simply not started. QuestObjective is an FName serialized as a
string — no-objective is the string "None", NEVER JSON null: the game's
JSON importer chokes on null and drops/corrupts the quest entries on load.
New entries created here mirror the game's own fresh entries (objective
"None", empty variable lists).

Rewards are granted the way the quest-flow blueprints do: items into free
Bag slots (Storage as overflow), recipe unlocks merged into RecipesUnlocked
(all reward recipe ids are verified strict-mode-safe), mounts merged into
MountsUnlockedList as bare MountDataAsset: refs.
"""
import re

from core import inventory as inv
from core.unlocks import merge_ids
from data.quest_data import EMBEDDED_QUESTS

STATE_NOT_STARTED = 0
STATE_IN_PROGRESS = 1
STATE_COMPLETED = 2
STATE_LABELS = {
    STATE_NOT_STARTED: "Not started",
    STATE_IN_PROGRESS: "In progress",
    STATE_COMPLETED: "Completed",
}
# Virtual state: Given (1) at the quest's final objective. The game only
# flips to Complete (2) at the turn-in conversation, so this leaves the
# turn-in — and the game's own reward grant — to the player.
READY_LABEL = "Ready to turn in"

# FName "None" — how the game serializes 'no current objective'
NO_OBJECTIVE = "None"

CATEGORY_LABELS = [
    ("main", "Main story"),
    ("side", "Side quests"),
    ("tutorial", "Tutorial"),
]


_ASSET_PREFIXES = ("RECIPE_", "ITEM_", "DA_Consumable_", "DA_Mount_", "DA_")


def pretty_asset(asset):
    """Readable label for a raw asset name, e.g.
    RECIPE_Masterworks_Weapon_GreatSword_TitansWrath ->
    'Masterworks Weapon Great Sword Titans Wrath'."""
    name = asset
    for p in _ASSET_PREFIXES:
        if name.startswith(p):
            name = name[len(p):]
            break
    words = []
    for part in name.split("_"):
        # split CamelCase runs: GreatSword -> Great Sword
        word = ""
        for ch in part:
            if word and ch.isupper() and not word[-1].isupper():
                words.append(word)
                word = ch
            else:
                word += ch
        if word:
            words.append(word)
    return " ".join(words) or asset


# --- objective story order -------------------------------------------------
# The dump preserves the quest asset's ObjectiveTexts map order — editor
# insertion order, not play order (Black Knight's Fortress lists its shard
# sub-steps after the ending). When every id in a quest is one numeric-
# suffixed family (Base_4, Base_4_13, ...) the numbers encode the real
# ladder: sub-steps nest under their parent, -1 is that level's intro step.
# Verified three ways for DR_Main: a real completed save ends at _6, the
# wiki walkthrough opens with Speak To Death (_-1), and every other numeric
# quest is already in this order. Mixed text ids keep dump order.

_OBJ_BASE = re.compile(r"^(.*?)(?:_?-?\d+)*$")
_OBJ_NUM = re.compile(r"-?\d+")


def _objective_sort_key(objective_id):
    # alternate str/int tokens, so comparisons never mix types
    key, pos = [], 0
    for m in _OBJ_NUM.finditer(objective_id):
        key.append(objective_id[pos:m.start()])
        key.append(int(m.group()))
        pos = m.end()
    key.append(objective_id[pos:])
    return key


def _story_order(objectives):
    if (len({_OBJ_BASE.match(o).group(1) for o in objectives}) != 1
            or not all(o[-1:].isdigit() for o in objectives)):
        return objectives
    return sorted(objectives, key=_objective_sort_key)


# Text ids carry no sortable structure; where the dump order is provably
# wrong the story order is pinned here (wiki walkthrough + the objective
# texts themselves — the dump listed 'Enter the Umbral Sands' 17th of 18
# and made FindLastKey the final objective instead of the turn-in).
# Applied only when the ids still match the dump exactly, so a game
# update that changes the quest falls back to dump order instead of
# dropping or inventing objectives.
_STORY_ORDER_OVERRIDES = {
    "Quest_UmS_MainQuest": [
        "EnterUmS",                # enter via the Door at The Bastion
        "LookForLife",             # signs of life -> Shangruuh
        "InvestigateGarouProblem",
        "ReturnToFirstGarou",
        "FindGarou",               # the Elder in the settlement south
        "SpeakToIcthlarin",        # Mirror Relay mission briefing
        "SpeakToGarouElder",       # start earning Alcarrid trust
        "FirstGarouEarnReputation.NoReputation",
        "FirstGarouEarnReputation.LowReputation",
        "FirstGarouEarnReputation.MediumReputation",
        "FirstGarouEarnReputation.HighReputation",
        "FirstGarouEarnReputation.MaxReputation",
        "FindThreeKeys",           # remaining camps' Mirror Lenses
        "FindLastKey",
        "RepairTheMirrors",
        "FightFuzan",              # enter the Fight Caves
        "SlayFuzan",               # journey through them to Fuzan
        "ReturnToIcthlarin",       # bring Fuzan's head — turn-in
    ],
}


for _q in EMBEDDED_QUESTS:
    _pinned = _STORY_ORDER_OVERRIDES.get(_q["asset"])
    if _pinned and sorted(_pinned) == sorted(_q["objectives"]):
        _q["objectives"] = list(_pinned)
    elif _q["objectives"]:
        _q["objectives"] = _story_order(_q["objectives"])


# Main-story progression in expansion order: Bramblemead -> Fellhollow ->
# Dowdun Reach -> Umbral Sands (Black Knight's Fortress "unlock[s] your way
# through to the Umbral Sands" per its own quest description).
MAIN_QUEST_ORDER = ["Quest_DragonSlayer", "Quest_DeathQuestMain",
                    "Quest_DR_MainQuest", "Quest_UmS_MainQuest"]


def quests(category=None):
    """Embedded quest list; main quests come in story order."""
    if category is None:
        return list(EMBEDDED_QUESTS)
    rows = [q for q in EMBEDDED_QUESTS if q["category"] == category]
    if category == "main":
        rows.sort(key=lambda q: MAIN_QUEST_ORDER.index(q["asset"])
                  if q["asset"] in MAIN_QUEST_ORDER else len(MAIN_QUEST_ORDER))
    return rows


def main_story_blockers(sf, quest):
    """Earlier main-story quests (names, in order) not yet Completed that
    block completing/turning in `quest`. Empty for non-main quests."""
    if quest["asset"] not in MAIN_QUEST_ORDER:
        return []
    states = get_states(sf)
    blockers = []
    for asset in MAIN_QUEST_ORDER[:MAIN_QUEST_ORDER.index(quest["asset"])]:
        pre = next(q for q in EMBEDDED_QUESTS if q["asset"] == asset)
        if states.get(pre["quest_id"]) != STATE_COMPLETED:
            blockers.append(pre["name"])
    return blockers


def main_story_uncomplete_blockers(sf, quest):
    """Later main-story quests (names, in order) still Completed that
    block downgrading `quest` out of Completed. Empty for non-main
    quests — the mirror of main_story_blockers."""
    if quest["asset"] not in MAIN_QUEST_ORDER:
        return []
    states = get_states(sf)
    blockers = []
    for asset in MAIN_QUEST_ORDER[MAIN_QUEST_ORDER.index(quest["asset"])
                                  + 1:]:
        later = next(q for q in EMBEDDED_QUESTS if q["asset"] == asset)
        if states.get(later["quest_id"]) == STATE_COMPLETED:
            blockers.append(later["name"])
    return blockers


def rewind_later_main_quests(sf, quest):
    """When `quest` becomes the active main-story point, later main
    quests that are In progress (or merely have a stale entry) can't
    legitimately coexist — remove their entries so only one main quest
    is running. Later Completed quests are left alone (the uncomplete
    blockers handle those). Returns the names of the quests reset."""
    if quest["asset"] not in MAIN_QUEST_ORDER:
        return []
    states = get_states(sf)
    reset = []
    for asset in MAIN_QUEST_ORDER[MAIN_QUEST_ORDER.index(quest["asset"])
                                  + 1:]:
        later = next(q for q in EMBEDDED_QUESTS if q["asset"] == asset)
        if (later["quest_id"] in states
                and states[later["quest_id"]] != STATE_COMPLETED):
            reset_quest(sf, later["quest_id"])
            reset.append(later["name"])
    return reset


def quest_by_id(quest_id):
    for q in EMBEDDED_QUESTS:
        if q["quest_id"] == quest_id:
            return q
    return None


def _quest_entries(sf, create=False):
    section = sf.progress.get("QuestProgress")
    if not isinstance(section, dict):
        if not create:
            return []
        section = {}
        sf.progress["QuestProgress"] = section
    entries = section.get("Quests")
    if not isinstance(entries, list):
        if not create:
            return []
        entries = []
        section["Quests"] = entries
    return entries


def get_states(sf):
    """{quest_id: QuestState} for every quest entry in the save."""
    states = {}
    for e in _quest_entries(sf):
        if isinstance(e, dict) and isinstance(e.get("QuestId"), str):
            states[e["QuestId"]] = e.get("QuestState", STATE_NOT_STARTED)
    return states


def get_objectives(sf):
    """{quest_id: QuestObjective} for every quest entry in the save.
    The game's no-objective marker "None" is read back as None."""
    objectives = {}
    for e in _quest_entries(sf):
        if isinstance(e, dict) and isinstance(e.get("QuestId"), str):
            obj = e.get("QuestObjective")
            objectives[e["QuestId"]] = None if obj == NO_OBJECTIVE else obj
    return objectives


def final_objective(quest):
    return quest["objectives"][-1] if quest["objectives"] else None


def objective_label(quest, objective_id):
    """Readable text for an objective id. Some quests store the text as
    the id itself, so fall back to the id."""
    return quest.get("objective_texts", {}).get(objective_id, objective_id)


def display_state(quest, state, objective):
    """Label for the UI, folding in the virtual ready-to-turn-in state."""
    if (state == STATE_IN_PROGRESS and quest["objectives"]
            and objective == final_objective(quest)):
        return READY_LABEL
    return STATE_LABELS[state]


_KEEP = object()


def set_state(sf, quest_id, state, objective=_KEEP):
    """Set a quest's state, creating its save entry if needed. Existing
    quest variables and objective are preserved unless `objective` is
    passed explicitly."""
    if state not in STATE_LABELS:
        raise ValueError("Unknown quest state: {}".format(state))
    entries = _quest_entries(sf, create=True)
    for e in entries:
        if isinstance(e, dict) and e.get("QuestId") == quest_id:
            e["QuestState"] = state
            if objective is not _KEEP:
                e["QuestObjective"] = (NO_OBJECTIVE if objective is None
                                       else objective)
            break
    else:
        entries.append({
            "QuestId": quest_id,
            "QuestState": state,
            "QuestObjective": (NO_OBJECTIVE if objective in (_KEEP, None)
                               else objective),
            "QuestInts": [],
            "QuestBools": [],
        })
    sf.mark_dirty()


def set_objective(sf, quest, objective_id):
    """Jump a quest to a rung on its objective ladder: In progress with
    `objective_id` as the current objective (everything before it on the
    ladder is implicitly done)."""
    if objective_id not in quest["objectives"]:
        raise ValueError("Unknown objective for {}: {}".format(
            quest["asset"], objective_id))
    set_state(sf, quest["quest_id"], STATE_IN_PROGRESS,
              objective=objective_id)


def set_in_progress(sf, quest):
    """Dropdown-style In progress. Coming down from Completed the kept
    objective would be the final one and wrongly read as Ready to turn
    in, so rewind to the first objective; otherwise keep the current
    objective."""
    if get_states(sf).get(quest["quest_id"]) == STATE_COMPLETED:
        first = quest["objectives"][0] if quest["objectives"] else None
        set_state(sf, quest["quest_id"], STATE_IN_PROGRESS, objective=first)
    else:
        set_state(sf, quest["quest_id"], STATE_IN_PROGRESS)


def reset_quest(sf, quest_id):
    """Remove a quest's save entry — the game's own representation of
    'not started', which also drops the stale objective and quest
    variables. Returns whether an entry existed."""
    entries = _quest_entries(sf)
    for i, e in enumerate(entries):
        if isinstance(e, dict) and e.get("QuestId") == quest_id:
            del entries[i]
            sf.mark_dirty()
            return True
    return False


def set_ready_to_turn_in(sf, quest):
    """Put a quest In progress at its final objective, so the player can
    turn it in at the NPC and receive the rewards from the game itself."""
    set_state(sf, quest["quest_id"], STATE_IN_PROGRESS,
              objective=final_objective(quest))


def complete_all(sf, category):
    """Mark every quest in a category Completed. Returns how many changed."""
    states = get_states(sf)
    changed = 0
    for q in quests(category):
        if states.get(q["quest_id"]) != STATE_COMPLETED:
            set_state(sf, q["quest_id"], STATE_COMPLETED)
            changed += 1
    return changed


def _free_bag_slots(sf):
    """Free Bag slot numbers, in order."""
    lo, hi = inv.slot_bounds("inventory", "Bag")
    used = inv.slots(sf, "inventory")
    return [slot for slot in range(lo, hi + 1) if slot not in used]


def _unlock_reward_mount(sf, asset):
    character = sf.progress.get("Character")
    if not isinstance(character, dict):
        return False
    mount = character.get("Mount")
    if not isinstance(mount, dict):
        mount = {}
        character["Mount"] = mount
    unlocked = mount.get("MountsUnlockedList")
    if not isinstance(unlocked, list):
        unlocked = []
    added = merge_ids(unlocked, ["MountDataAsset:" + asset])
    mount["MountsUnlockedList"] = unlocked
    return added > 0


def _unlock_reward_recipe(sf, recipe_id):
    progress = sf.progress.get("Progress")
    if not isinstance(progress, dict):
        progress = {}
        sf.progress["Progress"] = progress
    added = 0
    for key in ("RecipesUnlocked", "RecipesNew"):
        current = progress.get(key)
        current = current if isinstance(current, list) else []
        added += merge_ids(current, [recipe_id])
        progress[key] = current
    return added > 0


def grant_rewards(sf, quest):
    """Give a quest's rewards to the character. Reward items go into free
    Bag slots only — all or nothing: if the bag can't hold every item,
    NOTHING is granted and the caller is told to free up space first.

    Returns (granted, skipped): human-readable lists of what was added and
    what could not be (already owned unlocks, not enough bag space).
    """
    id_to_name, _, _, _ = inv.item_maps()
    granted, skipped = [], []
    free = _free_bag_slots(sf)
    needed = sum(1 for r in quest["rewards"]
                 if r["type"] == "item" and r["item_id"])
    if needed > len(free):
        return [], ["Not enough inventory space — this quest needs {} free "
                    "Bag slot{} (you have {}). Free up space first.".format(
                        needed, "s" if needed != 1 else "", len(free))]
    free = iter(free)
    for r in quest["rewards"]:
        label = id_to_name.get(r["item_id"]) if r["item_id"] else None
        label = label or pretty_asset(r["asset"])
        if r["type"] == "item":
            if not r["item_id"]:
                skipped.append(label)
                continue
            inv.set_slot(sf, "inventory", next(free), r["item_id"],
                         r["count"])
            granted.append("{}{}".format(
                label, " x{}".format(r["count"]) if r["count"] > 1 else ""))
        elif r["type"] == "recipe_unlock":
            if _unlock_reward_recipe(sf, r["item_id"]):
                granted.append("Recipe: {}".format(label))
            else:
                skipped.append("Recipe: {} (already unlocked)".format(label))
        elif r["type"] == "mount_unlock":
            if _unlock_reward_mount(sf, r["asset"]):
                granted.append("Mount: {}".format(r["asset"]))
            else:
                skipped.append("Mount: {} (already unlocked)".format(
                    r["asset"]))
    if granted:
        sf.mark_dirty()
    return granted, skipped
