import json
import os

from core.save_file import SaveFile
from core import skills

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


def test_tables_consistent():
    assert len(skills.SKILL_IDS) == len(skills.SKILL_LABELS) == 11
    assert len(skills.LEVEL_TO_XP) == 99
    assert skills.MAX_LEVEL_XP == 1000000


def test_level_math():
    assert skills.get_level_for_xp(0) == 1
    assert skills.get_level_for_xp(33) == 2
    assert skills.get_level_for_xp(1000000) == 99
    assert skills.get_level_for_xp(-5) == 1
    assert skills.get_level_for_xp("junk") == 1
    assert skills.get_xp_for_level(99) == 1000000
    assert skills.get_xp_for_level(1) == 0
    assert skills.get_xp_for_level(200) == 1000000


def test_get_skills_fills_missing_with_zero():
    rows = skills.get_skills(_sf())
    assert len(rows) == 11
    by_id = {r["id"]: r for r in rows}
    # fixture has Artisan maxed and Attack at 0; the other 9 default to 0
    assert by_id["Wf3i7Ha-B06DH719j1vtBw"]["level"] == 99
    assert by_id["4pefO9k1lUqfA6mvHNi1SA"]["xp"] == 0
    assert all(r["xp"] == 0 for r in rows if r["id"] not in
               ("Wf3i7Ha-B06DH719j1vtBw",))


def test_set_skill_xp_updates_and_appends():
    sf = _sf()
    skills.set_skill_xp(sf, "4pefO9k1lUqfA6mvHNi1SA", 500)   # existing entry
    skills.set_skill_xp(sf, "vwY5IkQJJDwb2PKEfoc8MQ", 1234)  # absent entry
    assert sf.dirty is True
    raw = sf.progress["Skills"]["Skills"]
    by_id = {s["Id"]: s["Xp"] for s in raw}
    assert by_id["4pefO9k1lUqfA6mvHNi1SA"] == 500
    assert by_id["vwY5IkQJJDwb2PKEfoc8MQ"] == 1234


def test_set_skill_xp_clamps_negative():
    sf = _sf()
    skills.set_skill_xp(sf, "4pefO9k1lUqfA6mvHNi1SA", -10)
    raw = {s["Id"]: s["Xp"] for s in sf.progress["Skills"]["Skills"]}
    assert raw["4pefO9k1lUqfA6mvHNi1SA"] == 0


def test_max_all_skills():
    sf = _sf()
    skills.max_all_skills(sf)
    rows = skills.get_skills(sf)
    assert all(r["level"] == 99 for r in rows)


def test_summarize_raw_dict():
    data = json.load(open(os.path.join(FIXTURES, "mini_full_save.json"),
                          encoding="utf-8"))
    total, maxed = skills.summarize(data)
    assert total == 99 + 1  # one maxed skill + one at level 1
    assert maxed == 1


def test_summarize_never_raises():
    assert skills.summarize(None) == (0, 0)
    assert skills.summarize({}) == (0, 0)
    assert skills.summarize({"GameProgress": {"Skills": "junk"}}) == (0, 0)
