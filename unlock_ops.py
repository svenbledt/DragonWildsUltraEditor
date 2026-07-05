"""GUI-free logic for the Unlocks tab's list-based unlockers.

Kept separate from tab_extra.py so it can be unit-tested without a Tk root.
Operates on the GameProgress-level save dict (the object setup_extra_tab
receives), reading and writing data["Progress"][<section>].
"""

BASE_MAX_HP = 100
HP_PER_SHRINE = 10


def merge_ids(current, ids):
    """Union `ids` into list `current` in place (order-stable, dedup).

    Returns the number of newly added ids. Existing entries are never
    removed or reordered.
    """
    seen = set(current)
    added = 0
    for i in ids:
        if i not in seen:
            current.append(i)
            seen.add(i)
            added += 1
    return added


def unlock_section(data, section_key, ids):
    """Union `ids` into data["Progress"][section_key] (created if absent).

    Never overwrites or deletes. Returns (added, total).
    """
    if not isinstance(data, dict):
        raise ValueError("no save loaded")
    progress = data.setdefault("Progress", {})
    current = progress.get(section_key)
    if not isinstance(current, list):
        current = []
    added = merge_ids(current, ids)
    progress[section_key] = current
    return added, len(current)


def is_fully_unlocked(data, section_key, ids):
    """True if every id in `ids` is already present in the save section."""
    ids = list(ids)
    if not ids:
        return False
    if not isinstance(data, dict):
        return False
    progress = data.get("Progress")
    if not isinstance(progress, dict):
        return False
    have = set(progress.get(section_key) or [])
    return set(ids).issubset(have)


def computed_max_hp(data):
    """Derived max HP = BASE_MAX_HP + HP_PER_SHRINE * len(ShrinesUnlocked)."""
    n = 0
    if isinstance(data, dict):
        progress = data.get("Progress")
        if isinstance(progress, dict):
            n = len(progress.get("ShrinesUnlocked") or [])
    return BASE_MAX_HP + HP_PER_SHRINE * n
