import json
import os
import pytest

from core.save_file import SaveFile, SaveError

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
