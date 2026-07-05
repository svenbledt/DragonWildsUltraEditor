"""Tk-free leveling math for RuneScape: Dragonwilds skills.

Mirrors the XP thresholds and level lookup in tab_skills.py. Kept as a separate,
dependency-free module because tab_skills.py imports tkinter, while info_summary
must stay importable without a display. tab_skills.py is intentionally left
unchanged (this feature makes no editing-logic changes); the shared table lives
here so new code has a single Tk-free source.
"""

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
