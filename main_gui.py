import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import theme
from tab_general import setup_general_tab
from tab_character import setup_character_tab
from tab_storage import setup_storage_tab
from tab_extra import setup_extra_tab
from tab_editor import setup_editor_tab

SETTINGS_FILE = "settings.json"


def get_progress_root(data):
    """Return the dict holding gameplay sections. As of 0.11 these live under a
    top-level "GameProgress" object; older saves stored them at the top level."""
    if isinstance(data, dict) and isinstance(data.get("GameProgress"), dict):
        return data["GameProgress"]
    return data


def get_default_save_path():
    user_dir = os.path.expanduser("~")
    return os.path.join(user_dir, "AppData", "Local", "RSDragonwilds", "Saved", "SaveCharacters")


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass


class DragonWildsUltraEditor(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)
        self.data = None
        self.filepath = None
        self.settings = load_settings()
        self.theme_mode = theme.current_mode(self.settings)
        self.palette = theme.apply_theme(master, self.theme_mode)
        self.create_widgets()
        self._repaint()

    def get_initial_dir(self):
        return self.settings.get("save_data_path", get_default_save_path())

    def _theme_button_text(self):
        # Show the mode the button switches TO.
        return "☀ Light" if self.theme_mode == theme.DARK else "☾ Dark"

    def create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Button(top, text="Load", command=self.load_file_dialog).pack(side="left")
        self.file_label = ttk.Label(top, text="No file loaded")
        self.file_label.pack(side="left", padx=12)
        ttk.Button(top, text="About", command=self.show_about_dialog).pack(side="right")
        ttk.Button(top, text="Settings", command=self.open_settings_dialog).pack(side="right", padx=(0, 8))
        self.theme_button = ttk.Button(top, text=self._theme_button_text(), command=self.toggle_theme)
        self.theme_button.pack(side="right", padx=(0, 8))

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.general_tab = ttk.Frame(self.notebook)
        self.name_tab = ttk.Frame(self.notebook)
        self.editor_tab = ttk.Frame(self.notebook)
        self.storage_tab = ttk.Frame(self.notebook)
        self.extra_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.general_tab, text="Info")
        self.notebook.add(self.name_tab, text="General")
        self.notebook.add(self.editor_tab, text="Inventory")
        self.notebook.add(self.storage_tab, text="Storage")
        self.notebook.add(self.extra_tab, text="Unlocks")

        self.setup_tabs()

    def set_status(self, msg):
        if hasattr(self, "status_var"):
            self.status_var.set(msg)

    def _repaint(self):
        pal = getattr(self, "palette", None)
        if pal:
            theme.paint_tree(self.master, pal)

    def toggle_theme(self):
        self.theme_mode = theme.LIGHT if self.theme_mode == theme.DARK else theme.DARK
        self.palette = theme.apply_theme(self.master, self.theme_mode)
        self.theme_button.config(text=self._theme_button_text())
        self.settings["theme"] = self.theme_mode
        save_settings(self.settings)
        self._repaint()
        self.set_status("Theme: {}".format(self.theme_mode))

    def save_json_func(self, data):
        # Tabs operate on the GameProgress sub-section, but the file on disk is
        # the full document. Always persist the complete self.data.
        data_to_save = self.data if self.data is not None else data
        if self.filepath:
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, indent=4)
                self.set_status("Saved {}".format(os.path.basename(self.filepath)))
                messagebox.showinfo("Success", "File saved:\n{}".format(self.filepath))
            except Exception as e:
                messagebox.showerror("Save Error", "Could not save file:\n{}".format(e))
        self.refresh_json_preview()

    def setup_tabs(self):
        progress = get_progress_root(self.data) if self.data is not None else None
        setup_general_tab(self.general_tab, self)
        setup_character_tab(self.name_tab, self)
        setup_editor_tab(self.editor_tab, progress, self.refresh_json_preview, self.save_json_func, self.refresh_inventory_and_storage)
        setup_storage_tab(self.storage_tab, progress, self.refresh_json_preview, self.save_json_func, self.refresh_inventory_and_storage, storage_slot_end=18)
        setup_extra_tab(self.extra_tab, progress, self.refresh_json_preview, self.save_json_func)
        self._repaint()

    def refresh_inventory_and_storage(self):
        progress = get_progress_root(self.data) if self.data is not None else None
        setup_editor_tab(self.editor_tab, progress, self.refresh_json_preview, self.save_json_func, self.refresh_inventory_and_storage)
        setup_storage_tab(self.storage_tab, progress, self.refresh_json_preview, self.save_json_func, self.refresh_inventory_and_storage, storage_slot_end=18)
        self._repaint()

    def load_save_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self.filepath = filepath
            self.setup_tabs()
            self.refresh_json_preview()
            self.file_label.config(text=os.path.basename(filepath))
            self.set_status("Loaded {}".format(os.path.basename(filepath)))
        except Exception as e:
            messagebox.showerror("Load Error", "Could not load file:\n{}".format(e))

    def load_file_dialog(self):
        initial_dir = self.get_initial_dir()
        filepath = filedialog.askopenfilename(
            title="Select Save File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if filepath:
            self.load_save_file(filepath)

    def save_file_dialog(self):
        if not self.filepath:
            initial_dir = self.get_initial_dir()
            filepath = filedialog.asksaveasfilename(
                title="Save File As",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=initial_dir
            )
            if not filepath:
                return
            self.filepath = filepath
        self.save_json_func(self.data)

    def open_settings_dialog(self):
        current_path = self.get_initial_dir()
        new_path = filedialog.askdirectory(
            title="Select Default Save Data Folder",
            initialdir=current_path
        )
        if new_path:
            self.settings["save_data_path"] = new_path
            save_settings(self.settings)
            messagebox.showinfo("Settings Saved", "Default save data path set to:\n{}".format(new_path))

    def refresh_json_preview(self):
        if self.data is not None and hasattr(self, "preview_text"):
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, json.dumps(self.data, indent=4))
            self.preview_text.config(state=tk.DISABLED)

    def show_about_dialog(self):
        features = [
            "Features:",
            "• View and edit your save file as JSON",
            "• Change character name and GUID",
            "• Edit skills from the Character tab",
            "• Fully editable inventory and storage (add, remove, bulk, filter, slot/amount, etc.)",
            "• Apply gear and storage presets",
            "• Editable loadout (inventory tab)",
            "• Filter and search item lists by name",
            "• Live JSON preview for all changes",
            "• Unlock recipes, buildings, mounts, picked-up items and Sanguine Urns",
            "• Resetting Health, Status Effects, etc.",
            "Shout out to Elleandria for the help",
            "Credits:",
            "DragonWilds Ultra Editor by TatsumaYakoshi",
        ]
        messagebox.showinfo("About — Features & Credits", "\n".join(features))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Wild Editor - Dragon Wilds Ultra")
    app = DragonWildsUltraEditor(root)
    app.mainloop()
