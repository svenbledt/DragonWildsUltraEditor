import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import uuid

from tab_skills import (
    SKILL_IDS,
    SKILL_LABELS,
    get_level_for_xp,
    get_xp_for_level,
)

MODE_OPTIONS = {
    "Normal": 0,
    "Hardcore": 1,
    "Creative": 3,
    "Custom": 4,
}

def _progress_root(data):
    """Skills live under top-level "GameProgress" as of the 0.11 update; fall
    back to the document itself for older saves. Kept local to avoid a circular
    import with main_gui."""
    if isinstance(data, dict) and isinstance(data.get("GameProgress"), dict):
        return data["GameProgress"]
    return data

def setup_character_tab(tab, editor):
    for widget in tab.winfo_children():
        widget.destroy()

    inner = ttk.Frame(tab)
    inner.pack(fill="both", expand=True)

    name_var = tk.StringVar()
    guid_var = tk.StringVar()
    mode_var = tk.StringVar(value="Normal")
    original_name = {"value": ""}
    original_mode = {"value": "Normal"}

    def find_first_value(data, key_name):
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key_name and isinstance(v, str):
                    return v
                result = find_first_value(v, key_name)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = find_first_value(item, key_name)
                if result is not None:
                    return result
        return None

    def update_all_char_names(data, new_name):
        if isinstance(data, dict):
            if "char_name" in data:
                data["char_name"] = new_name
            for value in data.values():
                update_all_char_names(value, new_name)
        elif isinstance(data, list):
            for item in data:
                update_all_char_names(item, new_name)

    def update_all_char_guids(data, new_guid):
        if isinstance(data, dict):
            if "char_guid" in data:
                data["char_guid"] = new_guid
            for value in data.values():
                update_all_char_guids(value, new_guid)
        elif isinstance(data, list):
            for item in data:
                update_all_char_guids(item, new_guid)

    def load_character_fields():
        if editor.data and isinstance(editor.data, dict):
            found_name = find_first_value(editor.data, "char_name")
            found_guid = find_first_value(editor.data, "char_guid")
            name_var.set(found_name if found_name is not None else "")
            guid_var.set(found_guid if found_guid is not None else "")
            original_name["value"] = name_var.get()

            meta = editor.data.get("meta_data", {})
            char_type = meta.get("char_type", 0)
            reverse_modes = {v: k for k, v in MODE_OPTIONS.items()}
            mode_var.set(reverse_modes.get(char_type, "Normal"))
            original_mode["value"] = mode_var.get()
        else:
            name_var.set("")
            guid_var.set("")
            mode_var.set("Normal")
            original_mode["value"] = "Normal"

    def randomize_guid():
        guid_var.set(uuid.uuid4().hex.upper())

    header = ttk.LabelFrame(inner, text="")
    header.pack(fill="x", padx=10, pady=(10, 8))

    ttk.Label(header, text="Name:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
    ttk.Entry(header, textvariable=name_var, width=36).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 6))

    ttk.Label(header, text="GUID:").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
    guid_entry = ttk.Entry(header, textvariable=guid_var, width=36)
    guid_entry.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 10))
    ttk.Button(header, text="Randomize", command=randomize_guid).grid(row=1, column=2, sticky="w", padx=(0, 10), pady=(0, 10))

    ttk.Label(header, text="Mode:").grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))
    mode_combo = ttk.Combobox(
        header,
        textvariable=mode_var,
        values=list(MODE_OPTIONS.keys()),
        width=18,
        state="readonly"
    )
    mode_combo.grid(row=2, column=1, sticky="w", padx=10, pady=(0, 10))

    skill_frame = ttk.LabelFrame(inner, text="")
    skill_frame.pack(fill="x", padx=10, pady=(0, 10))

    rows = []
    level_options = [str(i) for i in range(1, 100)]

    def build_skill_rows():
        for widget in skill_frame.winfo_children():
            widget.destroy()

        if not editor.data or not isinstance(editor.data, dict):
            ttk.Label(skill_frame, text="Load a save file to view and edit skills.").pack(padx=10, pady=10)
            return

        skill_container = _progress_root(editor.data).setdefault("Skills", {})
        skills_list = skill_container.setdefault("Skills", [])
        skill_map = {
            s.get("Id"): s
            for s in skills_list
            if isinstance(s, dict) and s.get("Id")
        }

        rows.clear()

        ttk.Label(skill_frame, text="Skill").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        ttk.Label(skill_frame, text="Level").grid(row=0, column=1, sticky="w", padx=8, pady=(8, 4))
        ttk.Label(skill_frame, text="XP").grid(row=0, column=2, sticky="w", padx=8, pady=(8, 4))

        for i, (skill_id, label) in enumerate(zip(SKILL_IDS, SKILL_LABELS), start=1):
            skill_data = skill_map.get(skill_id, {"Id": skill_id, "Xp": 0})

            try:
                xp = int(skill_data.get("Xp", 0))
            except Exception:
                xp = 0

            xp = max(0, xp)
            level = get_level_for_xp(xp)

            ttk.Label(skill_frame, text=label).grid(row=i, column=0, sticky="w", padx=8, pady=2)

            level_var = tk.StringVar(value=str(level))
            level_combo = ttk.Combobox(
                skill_frame,
                textvariable=level_var,
                values=level_options,
                width=8,
                state="normal"
            )
            level_combo.grid(row=i, column=1, padx=8, pady=2, sticky="w")

            xp_var = tk.StringVar(value=str(xp))
            xp_entry = ttk.Entry(skill_frame, textvariable=xp_var, width=12)
            xp_entry.grid(row=i, column=2, padx=8, pady=2, sticky="w")

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

    def apply_character_changes():
        new_name = name_var.get().strip()
        new_guid = guid_var.get().strip().upper()

        if not (editor.data and isinstance(editor.data, dict)):
            messagebox.showerror("Error", "No save loaded to update character data.")
            return

        if not new_name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return

        if not new_guid:
            messagebox.showerror("Error", "GUID cannot be empty.")
            return

        # Detect name or mode change
        selected_mode = mode_var.get()
        name_changed = new_name != original_name["value"]
        mode_changed = selected_mode != original_mode["value"]

        if name_changed or mode_changed:
            new_guid = uuid.uuid4().hex.upper()
            update_all_char_guids(editor.data, new_guid)
            guid_var.set(new_guid)

        update_all_char_names(editor.data, new_name)

        selected_mode = mode_var.get()
        char_type = MODE_OPTIONS.get(selected_mode, 0)
        meta = editor.data.setdefault("meta_data", {})
        meta["char_type"] = char_type

        skill_container = _progress_root(editor.data).setdefault("Skills", {})
        skills_list = skill_container.setdefault("Skills", [])
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

        original_name["value"] = new_name
        original_mode["value"] = selected_mode
        editor.refresh_json_preview()

        initial_dir = os.path.dirname(getattr(editor, "filepath", "") or os.getcwd())
        default_filename = f"{new_name}.json"

        save_path = filedialog.asksaveasfilename(
            title="Save your save file as...",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=initial_dir,
            initialfile=default_filename,
        )

        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(editor.data, f, indent=4, ensure_ascii=False)

                editor.filepath = save_path
                editor.refresh_json_preview()
                messagebox.showinfo(
                    "Success",
                    f"Character, GUID, and skills updated.\n\nSaved to:\n{save_path}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    build_skill_rows()

    ttk.Button(inner, text="Apply Changes", command=apply_character_changes).pack(pady=(0, 12))

    load_character_fields()
