import json
import os
import time
import pytest
from collections import OrderedDict

from core.save_file import (
    SaveFile, SaveError,
    BACKUP_KEEP, generate_guid, fix_max_slot_index, guidify_dict,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name):
    return SaveFile.load(os.path.join(FIXTURES, name))


def test_load_gameprogress_format():
    sf = _load_fixture("mini_full_save.json")
    assert sf.path.endswith("mini_full_save.json")
    assert sf.dirty is False
    # 0.11+ saves: progress root is the GameProgress sub-dict
    assert sf.progress is sf.data["GameProgress"]
    assert "Skills" in sf.progress


def test_load_old_format():
    sf = _load_fixture("mini_save.json")
    # old saves: the document itself is the progress root
    assert sf.progress is sf.data
    assert "Progress" in sf.progress


def test_load_rejects_non_json(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(SaveError):
        SaveFile.load(str(p))


def test_load_rejects_foreign_json(tmp_path):
    p = tmp_path / "other.json"
    p.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    with pytest.raises(SaveError):
        SaveFile.load(str(p))


def test_load_rejects_missing_file(tmp_path):
    with pytest.raises(SaveError):
        SaveFile.load(str(tmp_path / "nope.json"))


def test_mark_dirty():
    sf = _load_fixture("mini_save.json")
    sf.mark_dirty()
    assert sf.dirty is True


def _make_save(tmp_path):
    p = tmp_path / "char.json"
    p.write_text(json.dumps({"Progress": {}}), encoding="utf-8")
    return SaveFile.load(str(p))


def test_save_writes_backup_and_clears_dirty(tmp_path):
    sf = _make_save(tmp_path)
    sf.progress.setdefault("Progress", {})["RecipesUnlocked"] = ["a"]
    sf.mark_dirty()
    backup = sf.save()
    assert backup and os.path.exists(backup)
    assert sf.dirty is False
    on_disk = json.loads((tmp_path / "char.json").read_text(encoding="utf-8"))
    assert on_disk["Progress"]["RecipesUnlocked"] == ["a"]
    # backup holds the ORIGINAL content
    original = json.loads(open(backup, encoding="utf-8").read())
    assert "RecipesUnlocked" not in original["Progress"]
    # no temp file left behind
    assert not os.path.exists(str(tmp_path / "char.json") + ".tmp")


def test_backup_rotation_keeps_newest(tmp_path):
    sf = _make_save(tmp_path)
    for _ in range(BACKUP_KEEP + 3):
        sf.save()
    baks = [f for f in os.listdir(tmp_path) if ".bak-" in f]
    assert len(baks) == BACKUP_KEEP


def test_save_without_path_raises(tmp_path):
    sf = SaveFile({"Progress": {}})
    with pytest.raises(SaveError):
        sf.save()


def test_generate_guid_shape():
    g = generate_guid()
    assert isinstance(g, str) and len(g) == 22 and "=" not in g


def test_fix_max_slot_index_orders_and_trails():
    c = OrderedDict([("5", {"a": 1}), ("MaxSlotIndex", 99), ("2", {"b": 2})])
    fix_max_slot_index(c)
    assert list(c.keys()) == ["2", "5", "MaxSlotIndex"]
    assert c["MaxSlotIndex"] == 5


def test_fix_max_slot_index_empty():
    c = OrderedDict()
    fix_max_slot_index(c)
    assert c == OrderedDict([("MaxSlotIndex", -1)])


def test_guidify_adds_guids_but_skips_refs_and_marker():
    src = OrderedDict([
        ("0", {"ItemData": "x", "Count": 1}),
        ("1", {"PlayerInventoryItemIndex": 3}),
        ("MaxSlotIndex", 1),
    ])
    out = guidify_dict(src)
    assert "GUID" in out["0"] and len(out["0"]["GUID"]) == 22
    assert "GUID" not in out["1"]
    assert out["MaxSlotIndex"] == 1
    # source untouched
    assert "GUID" not in src["0"]
