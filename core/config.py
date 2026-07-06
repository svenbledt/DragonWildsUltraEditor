"""settings.json access — same file and keys as previous releases
(save_data_path, theme) plus first_run_done."""
import json

SETTINGS_FILE = "settings.json"


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            v = json.load(f)
            return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass
