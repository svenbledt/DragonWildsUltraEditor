import os

import pytest

from core.save_file import SaveFile
from core import character

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _sf():
    return SaveFile.load(os.path.join(FIXTURES, "mini_full_save.json"))


def _sf_with_guid():
    """The fixture has no char_guid key; set_identity only updates keys
    that already exist, so seed one for the identity tests."""
    sf = _sf()
    sf.data["Customization"]["char_guid"] = "A" * 32
    return sf


def test_getters():
    sf = _sf()
    assert character.get_name(sf.data) == "Testarossa"
    assert character.get_mode(sf.data) == "Creative"   # char_type 3
    assert character.get_guid(sf.data) == ""           # fixture has none


def test_getters_on_empty_dict():
    assert character.get_name({}) == character.DASH
    assert character.get_guid({}) == ""
    assert character.get_mode({}) == "Normal"


def test_getters_on_none():
    assert character.get_name(None) == character.DASH
    assert character.get_guid(None) == ""
    assert character.get_mode(None) == "Normal"


def test_mode_from_char_type():
    assert character.get_mode({"meta_data": {"char_type": 0}}) == "Normal"
    assert character.get_mode({"meta_data": {"char_type": 1}}) == "Hardcore"
    assert character.get_mode({"meta_data": {"char_type": 3}}) == "Creative"
    assert character.get_mode({"meta_data": {"char_type": 4}}) == "Custom"


def test_random_guid_shape():
    g = character.random_guid()
    assert len(g) == 32 and g == g.upper()
    assert all(c in "0123456789ABCDEF" for c in g)


def test_set_identity_same_name_keeps_guid():
    sf = _sf_with_guid()
    old_guid = character.get_guid(sf.data)
    written = character.set_identity(
        sf, character.get_name(sf.data), old_guid, character.get_mode(sf.data))
    assert written == old_guid
    assert sf.dirty is True


def test_set_identity_rename_regenerates_guid():
    sf = _sf_with_guid()
    old_guid = character.get_guid(sf.data)
    written = character.set_identity(sf, "NewName", old_guid, character.get_mode(sf.data))
    assert written != old_guid
    assert character.get_name(sf.data) == "NewName"
    assert character.get_guid(sf.data) == written


def test_set_identity_mode_change_regenerates_guid():
    sf = _sf_with_guid()
    old_guid = character.get_guid(sf.data)
    written = character.set_identity(sf, character.get_name(sf.data), old_guid, "Normal")
    assert written != old_guid
    assert sf.data["meta_data"]["char_type"] == 0


def test_set_identity_rejects_empty():
    sf = _sf()
    with pytest.raises(ValueError):
        character.set_identity(sf, "", "ABC", "Normal")
    with pytest.raises(ValueError):
        character.set_identity(sf, "Name", "", "Normal")


def test_set_identity_updates_nested_occurrences():
    sf = _sf_with_guid()
    character.set_identity(sf, "Zeta", character.get_guid(sf.data), character.get_mode(sf.data))

    def collect(d, key, acc):
        if isinstance(d, dict):
            for k, v in d.items():
                if k == key:
                    acc.append(v)
                collect(v, key, acc)
        elif isinstance(d, list):
            for v in d:
                collect(v, key, acc)
        return acc

    names = collect(sf.data, "char_name", [])
    assert names and all(n == "Zeta" for n in names)
