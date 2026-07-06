"""Character identity: name, GUID, game mode.

Mode is meta_data.char_type (0 Normal / 1 Hardcore / 3 Creative / 4 Custom).
Renaming or changing mode regenerates the GUID so the game treats the save
as a new character (avoids cloud-slot conflicts with the original).
"""
import uuid

MODE_OPTIONS = {"Normal": 0, "Hardcore": 1, "Creative": 3, "Custom": 4}
CHAR_TYPE_LABELS = {v: k for k, v in MODE_OPTIONS.items()}
DASH = "—"


def _find_first(data, key):
    """Depth-first search for the first occurrence of `key`."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                return v
            found = _find_first(v, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for v in data:
            found = _find_first(v, key)
            if found is not None:
                return found
    return None


def _update_all(data, key, value):
    """Set every occurrence of `key` anywhere in the document (the game
    stores char_name/char_guid in more than one place)."""
    if isinstance(data, dict):
        for k in data:
            if k == key:
                data[k] = value
            else:
                _update_all(data[k], key, value)
    elif isinstance(data, list):
        for v in data:
            _update_all(v, key, value)


def get_name(data):
    v = _find_first(data, "char_name")
    return v if isinstance(v, str) and v else DASH


def get_guid(data):
    v = _find_first(data, "char_guid")
    return v if isinstance(v, str) else ""


def get_mode(data):
    meta = data.get("meta_data") if isinstance(data, dict) else None
    char_type = meta.get("char_type") if isinstance(meta, dict) else None
    try:
        char_type = int(char_type)
    except (TypeError, ValueError):
        char_type = 0
    return CHAR_TYPE_LABELS.get(char_type, "Normal")


def random_guid():
    return uuid.uuid4().hex.upper()


def set_identity(sf, name, guid, mode_label):
    """Apply name/GUID/mode to the save. Returns the GUID actually written
    (a fresh one when name or mode changed)."""
    name = (name or "").strip()
    guid = (guid or "").strip().upper()
    if not name:
        raise ValueError("Name cannot be empty.")
    if not guid:
        raise ValueError("GUID cannot be empty.")
    changed = (name != get_name(sf.data)
               or mode_label != get_mode(sf.data))
    if changed:
        guid = random_guid()
    _update_all(sf.data, "char_name", name)
    _update_all(sf.data, "char_guid", guid)
    meta = sf.data.setdefault("meta_data", {})
    if isinstance(meta, dict):
        meta["char_type"] = MODE_OPTIONS.get(mode_label, 0)
    sf.mark_dirty()
    return guid
