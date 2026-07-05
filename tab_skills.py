import tkinter as tk
from tkinter import ttk, messagebox
import json


SKILL_IDS = [
    'Wf3i7Ha-B06DH719j1vtBw', '4pefO9k1lUqfA6mvHNi1SA', 'waK-8EyQFQ2xEjCGYmuTRQ',
    'Tn7t6DQyX0-Q0cM5K7B90A', '0hreSMRVXUihq9qjDO2CFA', 'jqX0Gh6QI0GFFPCDFK_CJQ',
    'heq7u88Q2UuLXFqLGTVwQw', 'NOqC-z-2ckqi0El22qMFlw', '4zYUGF5u_0KbMLkWJmmBbQ', 'PyUi-0LU_riFY46AnnFiWg',
    'vwY5IkQJJDwb2PKEfoc8MQ'  # Fishing (added in the 0.11 / Anniversary update)
]

SKILL_LABELS = [
    "Artisan XP", "Attack XP", "Construction XP", "Cooking XP",
    "Magic XP", "Mining XP", "Ranged XP", "Runecrafting XP", "Woodcutting XP", "Farming XP",
    "Fishing XP"
]

# RuneScape: Dragonwilds XP thresholds for levels 1-99
LEVEL_TO_XP = [
    0, 33, 70, 111, 156, 206, 261, 322, 389, 463,
    545, 636, 736, 847, 969, 1104, 1253, 1417, 1598, 1798,
    2018, 2261, 2529, 2825, 3152, 3512, 3910, 4349, 4833, 5367,
    5957, 6608, 7326, 8118, 8993, 9958, 11023, 12199, 13496, 14929,
    16510, 18255, 20181, 22307, 24654, 27245, 30105, 33262, 36747, 40594,
    44581, 48717, 52997, 57421, 61990, 66702, 71560, 76562, 81708, 86998,
    92433, 98012, 103735, 109603, 115616, 121772, 128073, 134518, 141108, 147842,
    154721, 161743, 168910, 176222, 183678, 191278, 199022, 206911, 214944, 223122,
    231444, 239910, 248521, 257276, 266176, 275219, 284407, 293740, 303217, 312838,
    322604, 332514, 342568, 395129, 447689, 543044, 666881, 819200, 1000000
]


def get_level_for_xp(xp):
    try:
        xp = int(xp)
    except Exception:
        xp = 0

    xp = max(0, xp)

    for i in range(len(LEVEL_TO_XP) - 1, -1, -1):
        if xp >= LEVEL_TO_XP[i]:
            return i + 1

    return 1


def get_xp_for_level(level):
    try:
        level = int(level)
    except Exception:
        level = 1

    level = max(1, min(99, level))
    return LEVEL_TO_XP[level - 1]


def try_save_file(data, save_json_func=None, refresh_preview=None):
    if callable(save_json_func):
        try:
            save_json_func(data)
            return True
        except Exception:
            return False

    owner = getattr(refresh_preview, "__self__", None)
    filepath = getattr(owner, "filepath", None) if owner is not None else None

    if filepath:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    return False


def setup_skills_tab(tab, data, refresh_preview, save_json_func=None):
    for widget in tab.winfo_children():
        widget.destroy()

    if not data or not isinstance(data, dict):
        ttk.Label(tab, text="Load a save file to view and edit skills.").pack(padx=10, pady=10)
        return

    skill_container = data.setdefault("Skills", {})
    skills_list = skill_container.setdefault("Skills", [])

    # Build map only from valid skill entries
    skill_map = {
        s.get("Id"): s
        for s in skills_list
        if isinstance(s, dict) and s.get("Id")
    }

    rows = []
    level_options = [str(i) for i in range(1, 100)]

    ttk.Label(tab, text="Skills").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 4))
    ttk.Label(tab, text="Level").grid(row=0, column=1, sticky="w", padx=5, pady=(5, 4))
    ttk.Label(tab, text="XP").grid(row=0, column=2, sticky="w", padx=5, pady=(5, 4))

    for i, (skill_id, label) in enumerate(zip(SKILL_IDS, SKILL_LABELS), start=1):
        skill_data = skill_map.get(skill_id, {"Id": skill_id, "Xp": 0})

        try:
            xp = int(skill_data.get("Xp", 0))
        except Exception:
            xp = 0

        xp = max(0, xp)
        level = get_level_for_xp(xp)

        ttk.Label(tab, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=2)

        level_var = tk.StringVar(value=str(level))
        level_combo = ttk.Combobox(
            tab,
            textvariable=level_var,
            values=level_options,
            width=8,
            state="normal"
        )
        level_combo.grid(row=i, column=1, padx=5, pady=2, sticky="w")

        xp_var = tk.StringVar(value=str(xp))
        xp_entry = ttk.Entry(tab, textvariable=xp_var, width=12)
        xp_entry.grid(row=i, column=2, padx=5, pady=2, sticky="w")

        def on_level_change(event=None, level_var=level_var, xp_var=xp_var):
            value = level_var.get().strip()
            if value == "":
                return

            try:
                typed_level = int(value)
            except ValueError:
                return

            typed_level = max(1, min(99, typed_level))
            level_var.set(str(typed_level))
            xp_var.set(str(get_xp_for_level(typed_level)))

        def on_xp_change(event=None, xp_var=xp_var, level_var=level_var):
            value = xp_var.get().strip()
            if value == "":
                return

            try:
                typed_xp = int(value)
            except ValueError:
                return

            typed_xp = max(0, typed_xp)
            xp_var.set(str(typed_xp))
            level_var.set(str(get_level_for_xp(typed_xp)))

        level_combo.bind("<<ComboboxSelected>>", on_level_change)
        level_combo.bind("<KeyRelease>", on_level_change)
        level_combo.bind("<FocusOut>", on_level_change)

        xp_entry.bind("<KeyRelease>", on_xp_change)
        xp_entry.bind("<FocusOut>", on_xp_change)

        rows.append((skill_id, xp_var, level_var))

    def apply_changes():
        # Rebuild the map in case the underlying list changed elsewhere
        current_skill_map = {
            s.get("Id"): s
            for s in skills_list
            if isinstance(s, dict) and s.get("Id")
        }

        for skill_id, xp_var, level_var in rows:
            xp_text = xp_var.get().strip()

            try:
                xp = int(xp_text) if xp_text else 0
            except ValueError:
                xp = 0

            xp = max(0, xp)
            level = get_level_for_xp(xp)

            if skill_id in current_skill_map:
                current_skill_map[skill_id]["Xp"] = xp
            else:
                new_entry = {"Id": skill_id, "Xp": xp}
                skills_list.append(new_entry)
                current_skill_map[skill_id] = new_entry

            xp_var.set(str(xp))
            level_var.set(str(level))

        refresh_preview()
        saved = try_save_file(data, save_json_func=save_json_func, refresh_preview=refresh_preview)

        if saved:
            try:
                messagebox.showinfo("Success", "XP changes applied and file saved.")
            except Exception:
                pass
        else:
            try:
                messagebox.showerror("Error", "XP changes were applied, but the file could not be saved.")
            except Exception:
                pass

    ttk.Button(tab, text="Apply XP", command=apply_changes).grid(
        row=len(SKILL_IDS) + 1,
        column=0,
        columnspan=3,
        pady=10
    )
