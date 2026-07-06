"""Skill ids, XP<->level math, and skill read/write operations.

Skills live at <progress-root>.Skills.Skills as {"Id", "Xp"} entries.
LEVEL_TO_XP mirrors the game's thresholds for levels 1-99.
"""

SKILL_IDS = [
    "Wf3i7Ha-B06DH719j1vtBw", "4pefO9k1lUqfA6mvHNi1SA", "waK-8EyQFQ2xEjCGYmuTRQ",
    "Tn7t6DQyX0-Q0cM5K7B90A", "0hreSMRVXUihq9qjDO2CFA", "jqX0Gh6QI0GFFPCDFK_CJQ",
    "heq7u88Q2UuLXFqLGTVwQw", "NOqC-z-2ckqi0El22qMFlw", "4zYUGF5u_0KbMLkWJmmBbQ",
    "PyUi-0LU_riFY46AnnFiWg",
    "vwY5IkQJJDwb2PKEfoc8MQ",  # Fishing (added in the 0.11 update)
]

SKILL_LABELS = [
    "Artisan", "Attack", "Construction", "Cooking", "Magic", "Mining",
    "Ranged", "Runecrafting", "Woodcutting", "Farming", "Fishing",
]

LEVEL_TO_XP = [
    0, 33, 70, 111, 156, 206, 261, 322, 389, 463,
    545, 636, 736, 847, 969, 1104, 1253, 1417, 1598, 1798,
    2018, 2261, 2529, 2825, 3152, 3512, 3910, 4349, 4833, 5367,
    5957, 6608, 7326, 8118, 8993, 9958, 11023, 12199, 13496, 14929,
    16510, 18255, 20181, 22307, 24654, 27245, 30105, 33262, 36747, 40594,
    44581, 48717, 52997, 57421, 61990, 66702, 71560, 76562, 81708, 86998,
    92433, 98012, 103735, 109603, 115616, 121772, 128073, 134518, 141108, 147842,
    154721, 161743, 168910, 176222, 183678, 191278, 199022, 206911, 214944, 223122,
    231444, 239910, 248521, 257276, 266176, 275219, 284407, 293740, 303217, 312838,
    322604, 332514, 342568, 395129, 447689, 543044, 666881, 819200, 1000000,
]

MAX_LEVEL_XP = LEVEL_TO_XP[-1]


def get_level_for_xp(xp):
    try:
        xp = int(xp)
    except Exception:
        xp = 0
    xp = max(0, xp)
    for i in range(len(LEVEL_TO_XP) - 1, -1, -1):
        if xp >= LEVEL_TO_XP[i]:
            return i + 1
    return 1


def get_xp_for_level(level):
    try:
        level = int(level)
    except Exception:
        level = 1
    level = max(1, min(99, level))
    return LEVEL_TO_XP[level - 1]


def _skills_list(progress):
    container = progress.setdefault("Skills", {})
    if not isinstance(container, dict):
        container = {}
        progress["Skills"] = container
    lst = container.setdefault("Skills", [])
    if not isinstance(lst, list):
        lst = []
        container["Skills"] = lst
    return lst


def get_skills(sf):
    """One row per known skill: {"id","label","xp","level"}; missing
    entries read as 0 XP."""
    have = {}
    for s in _skills_list(sf.progress):
        if isinstance(s, dict) and s.get("Id"):
            have[s["Id"]] = s
    rows = []
    for sid, label in zip(SKILL_IDS, SKILL_LABELS):
        try:
            xp = max(0, int(have.get(sid, {}).get("Xp", 0)))
        except Exception:
            xp = 0
        rows.append({"id": sid, "label": label, "xp": xp,
                     "level": get_level_for_xp(xp)})
    return rows


def set_skill_xp(sf, skill_id, xp):
    xp = max(0, int(xp))
    lst = _skills_list(sf.progress)
    for s in lst:
        if isinstance(s, dict) and s.get("Id") == skill_id:
            s["Xp"] = xp
            break
    else:
        lst.append({"Id": skill_id, "Xp": xp})
    sf.mark_dirty()


def max_all_skills(sf):
    for sid in SKILL_IDS:
        set_skill_xp(sf, sid, MAX_LEVEL_XP)


def summarize(data):
    """(total_level, maxed_count) from a RAW save dict; never raises.
    Used by the character picker, which must not blow up on odd files."""
    if not isinstance(data, dict):
        return (0, 0)
    root = data.get("GameProgress") if isinstance(data.get("GameProgress"), dict) else data
    container = root.get("Skills") if isinstance(root, dict) else None
    lst = container.get("Skills") if isinstance(container, dict) else None
    if not isinstance(lst, list):
        return (0, 0)
    total = maxed = 0
    for s in lst:
        if not isinstance(s, dict):
            continue
        lvl = get_level_for_xp(s.get("Xp", 0))
        total += lvl
        if lvl >= 99:
            maxed += 1
    return (total, maxed)
