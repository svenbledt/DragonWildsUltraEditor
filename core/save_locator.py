"""Find the game's save folder and summarize character files for the
picker. Must never raise: odd files in the folder are simply skipped."""
import json
import os

from core import character, skills


def default_save_dir():
    return os.path.join(os.path.expanduser("~"), "AppData", "Local",
                        "RSDragonwilds", "Saved", "SaveCharacters")


def list_characters(folder):
    """[{path, name, mode, total_level, maxed, mtime}] for every character
    save in `folder`, newest first."""
    out = []
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return out
    for e in entries:
        if not e.name.lower().endswith(".json"):
            continue
        try:
            if not e.is_file():
                continue
            with open(e.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        looks_like_save = any(isinstance(data.get(k), dict) for k in
                              ("GameProgress", "Progress", "Character"))
        if not looks_like_save:
            continue
        total, maxed = skills.summarize(data)
        try:
            mtime = e.stat().st_mtime
        except OSError:
            mtime = 0
        out.append({
            "path": e.path,
            "name": character.get_name(data),
            "mode": character.get_mode(data),
            "total_level": total,
            "maxed": maxed,
            "mtime": mtime,
        })
    out.sort(key=lambda c: c["mtime"], reverse=True)
    return out
