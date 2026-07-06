"""Quest progress operations on GameProgress.QuestProgress.

Save layout (verified against real saves + game files):
Quests[] entries: {QuestId, QuestState, QuestObjective, QuestInts, QuestBools}.
QuestState is EQuestState: 0=Ungiven, 1=Given, 2=Complete. A quest with no
entry is simply not started. New entries created here mirror the game's own
fresh entries (objective None, empty variable lists).

Rewards are granted the way the quest-flow blueprints do: items into free
Bag slots (Storage as overflow), recipe unlocks merged into RecipesUnlocked
(all reward recipe ids are verified strict-mode-safe), mounts merged into
MountsUnlockedList as bare MountDataAsset: refs.
"""
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


def quests(category=None):
    """Embedded quest list (already sorted main/side/tutorial, by name)."""
    if category is None:
        return list(EMBEDDED_QUESTS)
    return [q for q in EMBEDDED_QUESTS if q["category"] == category]


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


def set_state(sf, quest_id, state):
    """Set a quest's state, creating its save entry if needed."""
    if state not in STATE_LABELS:
        raise ValueError("Unknown quest state: {}".format(state))
    entries = _quest_entries(sf, create=True)
    for e in entries:
        if isinstance(e, dict) and e.get("QuestId") == quest_id:
            e["QuestState"] = state
            break
    else:
        entries.append({
            "QuestId": quest_id,
            "QuestState": state,
            "QuestObjective": None,
            "QuestInts": [],
            "QuestBools": [],
        })
    sf.mark_dirty()


def complete_all(sf, category):
    """Mark every quest in a category Completed. Returns how many changed."""
    states = get_states(sf)
    changed = 0
    for q in quests(category):
        if states.get(q["quest_id"]) != STATE_COMPLETED:
            set_state(sf, q["quest_id"], STATE_COMPLETED)
            changed += 1
    return changed


def _free_slots(sf):
    """Free Bag slots first, then free Storage slots, in order."""
    lo, hi = inv.slot_bounds("inventory", "Bag")
    used = inv.slots(sf, "inventory")
    for slot in range(lo, hi + 1):
        if slot not in used:
            yield "inventory", slot
    lo, hi = inv.STORAGE_RANGE
    used = inv.slots(sf, "storage")
    for slot in range(lo, hi + 1):
        if slot not in used:
            yield "storage", slot


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
    """Give a quest's rewards to the character.

    Returns (granted, skipped): human-readable lists of what was added and
    what could not be (already owned unlocks, no free slots).
    """
    id_to_name, _, _, _ = inv.item_maps()
    granted, skipped = [], []
    free = _free_slots(sf)
    for r in quest["rewards"]:
        label = id_to_name.get(r["item_id"]) if r["item_id"] else None
        label = label or pretty_asset(r["asset"])
        if r["type"] == "item":
            if not r["item_id"]:
                skipped.append(label)
                continue
            try:
                where, slot = next(free)
            except StopIteration:
                skipped.append("{} (no free slot)".format(label))
                continue
            inv.set_slot(sf, where, slot, r["item_id"], r["count"])
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
