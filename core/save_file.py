"""Save-file model: loading, validation, dirty tracking, safe saving.

The only module in the app allowed to read or write character-save JSON
on disk.
"""
import json


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
            raise SaveError("Could not read this file:\n{}".format(e))
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
