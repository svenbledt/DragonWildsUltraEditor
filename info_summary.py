"""Pure, Tk-free character-summary extraction for the Info tab.

Operates on the full save document (main_gui's self.data): the character name is
a nested "char_name" value, mode is the top-level "Hardcore" flag, and skills
live at <progress_root>.Skills.Skills as {"Id", "Xp"} entries. Every field
degrades to a dash / 0 on missing or malformed data; build_summary never raises.
"""
from leveling import get_level_for_xp

DASH = "—"  # em dash, shown for unknown fields

# Skill data-asset ids (mirrors tab_skills.SKILL_IDS). len() is the summary total.
SKILL_IDS = [
    "Wf3i7Ha-B06DH719j1vtBw", "4pefO9k1lUqfA6mvHNi1SA", "waK-8EyQFQ2xEjCGYmuTRQ",
    "Tn7t6DQyX0-Q0cM5K7B90A", "0hreSMRVXUihq9qjDO2CFA", "jqX0Gh6QI0GFFPCDFK_CJQ",
    "heq7u88Q2UuLXFqLGTVwQw", "NOqC-z-2ckqi0El22qMFlw", "4zYUGF5u_0KbMLkWJmmBbQ",
    "PyUi-0LU_riFY46AnnFiWg", "vwY5IkQJJDwb2PKEfoc8MQ",
]


def find_first_value(data, key):
    """Recursively return the first value stored under `key`, or None."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                return v
            found = find_first_value(v, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_first_value(item, key)
            if found is not None:
                return found
    return None


def _progress_root(data):
    if isinstance(data, dict) and isinstance(data.get("GameProgress"), dict):
        return data["GameProgress"]
    return data


def build_summary(data):
    empty = {"name": DASH, "mode": DASH, "total_level": 0,
             "maxed_skills": 0, "skill_count": len(SKILL_IDS)}
    if not isinstance(data, dict):
        return empty

    name = find_first_value(data, "char_name")
    name = name if isinstance(name, str) and name else DASH

    hc = data.get("Hardcore")
    mode = DASH if hc is None else ("Hardcore" if hc else "Normal")

    root = _progress_root(data)
    skills = []
    if isinstance(root, dict):
        container = root.get("Skills")
        if isinstance(container, dict) and isinstance(container.get("Skills"), list):
            skills = container["Skills"]

    total = 0
    maxed = 0
    for s in skills:
        if not isinstance(s, dict):
            continue
        lvl = get_level_for_xp(s.get("Xp", 0))
        total += lvl
        if lvl >= 99:
            maxed += 1

    return {"name": name, "mode": mode, "total_level": total,
            "maxed_skills": maxed, "skill_count": len(SKILL_IDS)}
