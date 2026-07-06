"""Save-file model: loading, validation, dirty tracking, safe saving.

The only module in the app allowed to read or write character-save JSON
on disk.
"""
import base64
import json
import os
from collections import OrderedDict
from datetime import datetime

BACKUP_KEEP = 5


def generate_guid():
    """22-char url-safe id, the same shape the game stores per item entry."""
    return base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("=")


def fix_max_slot_index(container):
    """Normalize an item container in place: numeric slot keys sorted
    ascending, then a trailing MaxSlotIndex equal to the highest used slot
    (-1 when empty). The game expects exactly this shape."""
    slot_keys = [int(k) for k in container.keys()
                 if isinstance(k, str) and k.isdigit()]
    max_slot = max(slot_keys) if slot_keys else -1
    items_part = [(k, v) for k, v in container.items() if k != "MaxSlotIndex"]
    fixed = OrderedDict(sorted(
        items_part, key=lambda x: int(x[0]) if x[0].isdigit() else -1))
    fixed["MaxSlotIndex"] = max_slot
    container.clear()
    container.update(fixed)


def guidify_dict(d):
    """Copy of container `d` where every item entry gets a fresh GUID.
    Entries that only reference an inventory slot (PlayerInventoryItemIndex)
    and the MaxSlotIndex marker are copied untouched."""
    out = OrderedDict()
    for k, v in d.items():
        if isinstance(v, dict):
            entry = dict(v)
            if "PlayerInventoryItemIndex" not in entry and k != "MaxSlotIndex":
                entry["GUID"] = generate_guid()
            out[k] = entry
        else:
            out[k] = v
    return out


class SaveError(Exception):
    """A user-presentable problem with a save file."""


class SaveFile:
    def __init__(self, data, path=None):
        self.data = data
        self.path = path
        self.dirty = False

    @classmethod
    def load(cls, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise SaveError(
                "This file couldn't be opened or isn't readable JSON, "
                "so it can't be loaded as a save.\n"
                "(Technical detail: {})".format(e)
            )
        if not isinstance(data, dict) or not (
            isinstance(data.get("GameProgress"), dict)
            or isinstance(data.get("Progress"), dict)
            or isinstance(data.get("Character"), dict)
        ):
            raise SaveError(
                "This does not look like a Dragonwilds character save."
            )
        return cls(data, path)

    @property
    def progress(self):
        """The dict holding gameplay sections: "GameProgress" on 0.11+
        saves, the document itself on older ones."""
        if isinstance(self.data.get("GameProgress"), dict):
            return self.data["GameProgress"]
        return self.data

    def mark_dirty(self):
        self.dirty = True

    def save(self):
        """Write the save safely: back up the current file first, then write
        to a temp file and atomically replace. Returns the backup path
        (None when the file didn't exist yet). Clears `dirty` on success."""
        if not self.path:
            raise SaveError("No file path set.")
        backup = None
        if os.path.exists(self.path):
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = "{}.bak-{}".format(self.path, stamp)
            n = 1
            while os.path.exists(backup):
                backup = "{}.bak-{}-{}".format(self.path, stamp, n)
                n += 1
            with open(self.path, "rb") as src, open(backup, "wb") as dst:
                dst.write(src.read())
            self._prune_backups()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, self.path)
        self.dirty = False
        return backup

    def _prune_backups(self):
        folder = os.path.dirname(self.path) or "."
        prefix = os.path.basename(self.path) + ".bak-"
        baks = sorted(fn for fn in os.listdir(folder) if fn.startswith(prefix))
        for fn in baks[:-BACKUP_KEEP]:
            try:
                os.remove(os.path.join(folder, fn))
            except OSError:
                pass
