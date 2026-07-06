import json
import os
import time

from core import save_locator


def _write(folder, name, payload):
    p = os.path.join(folder, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return p


def test_default_dir_shape():
    d = save_locator.default_save_dir()
    assert d.endswith(os.path.join("RSDragonwilds", "Saved", "SaveCharacters"))


def test_missing_folder_returns_empty(tmp_path):
    assert save_locator.list_characters(str(tmp_path / "nope")) == []


def test_lists_only_character_saves(tmp_path):
    good = {
        "meta_data": {"char_type": 3},
        "Customization": {"char_name": "Picker"},
        "GameProgress": {"Skills": {"Skills": [
            {"Id": "Wf3i7Ha-B06DH719j1vtBw", "Xp": 1000000}]}},
    }
    _write(str(tmp_path), "hero.json", good)
    _write(str(tmp_path), "junk.json", {"unrelated": True})
    (tmp_path / "broken.json").write_text("{oops", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("hi", encoding="utf-8")

    chars = save_locator.list_characters(str(tmp_path))
    assert len(chars) == 1
    c = chars[0]
    assert c["name"] == "Picker"
    assert c["mode"] == "Creative"
    assert c["total_level"] == 99
    assert c["maxed"] == 1
    assert c["path"].endswith("hero.json")


def test_sorted_newest_first(tmp_path):
    base = {"GameProgress": {}, "Customization": {"char_name": "X"}}
    old = _write(str(tmp_path), "old.json", base)
    _write(str(tmp_path), "new.json", base)
    past = time.time() - 3600
    os.utime(old, (past, past))
    chars = save_locator.list_characters(str(tmp_path))
    assert [os.path.basename(c["path"]) for c in chars] == ["new.json", "old.json"]
