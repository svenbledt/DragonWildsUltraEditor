"""Main application window: header, sidebar, page switching, save flow."""
import importlib
import os

import customtkinter as ctk
from tkinter import messagebox

from core import config, character, skills
from core.save_file import SaveFile, SaveError
from ui.icons import app_root

APP_TITLE = "DragonWilds Ultra Editor"
APP_VERSION = "13.0"

# key -> (sidebar label, module path, class name); modules imported lazily so
# the shell runs before all pages exist.
PAGES = [
    ("overview", "Overview", "ui.pages.overview", "OverviewPage"),
    ("character", "Character", "ui.pages.character", "CharacterPage"),
    ("skills", "Skills", "ui.pages.skills", "SkillsPage"),
    ("inventory", "Inventory", "ui.pages.inventory", "InventoryPage"),
    ("storage", "Storage", "ui.pages.storage", "StoragePage"),
    ("quests", "Quests", "ui.pages.quests", "QuestsPage"),
    ("unlocks", "Unlocks", "ui.pages.unlocks", "UnlocksPage"),
]

ABOUT_TEXT = (
    "A comprehensive save editor for RuneScape: Dragonwilds — edit your "
    "character, skills, inventory, storage and unlocks. Changes are only "
    "written when you press Save, and a backup is created every time.\n\n"
    "This release continues the work of the original creator, "
    "TatsumaYakoshi, carrying the project forward with a redesigned "
    "interface, new features and an expanded unlock set."
)

ABOUT_CREDITS = (
    "Credits\n"
    "• Originally created by TatsumaYakoshi\n"
    "• Continued & maintained by TailwindDev\n"
    "• Shout out to Elleandria for the help\n\n"
    "Not affiliated with Jagex."
)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = config.load_settings()
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        self.title(APP_TITLE)
        self.geometry("1040x680")
        self.minsize(900, 600)
        try:
            self.iconbitmap(os.path.join(app_root(), "Dragonwilds_Editor.ico"))
        except Exception:
            pass

        self.save = None            # SaveFile | None
        self._pages = {}            # key -> page instance
        self._nav_buttons = {}
        self._current = None

        self._build_header()
        self._build_body()
        self._build_statusbar()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_picker()
        if not self.settings.get("first_run_done"):
            self.settings["first_run_done"] = True
            config.save_settings(self.settings)
            self.after(300, self.show_about)

    # ---------- layout ----------
    def _build_header(self):
        h = ctk.CTkFrame(self, height=56, corner_radius=0)
        h.pack(fill="x", side="top")
        h.pack_propagate(False)
        self.header_name = ctk.CTkLabel(
            h, text=APP_TITLE, font=ctk.CTkFont(size=17, weight="bold"))
        self.header_name.pack(side="left", padx=16)
        self.header_mode = ctk.CTkLabel(
            h, text="", fg_color=("gray80", "gray25"), corner_radius=10,
            padx=10)
        self.header_level = ctk.CTkLabel(
            h, text="", fg_color=("gray80", "gray25"), corner_radius=10,
            padx=10)
        self.save_button = ctk.CTkButton(
            h, text="Save", width=110, state="disabled", command=self.do_save)
        self.save_button.pack(side="right", padx=16)
        self.dirty_label = ctk.CTkLabel(
            h, text="", text_color="#e8b339",
            font=ctk.CTkFont(size=12, weight="bold"))
        self.dirty_label.pack(side="right", padx=8)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self.sidebar = ctk.CTkFrame(body, width=170, corner_radius=0)
        self.sidebar.pack_propagate(False)
        for key, label, _, _ in PAGES:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w", height=38,
                corner_radius=6, fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn
        foot = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        foot.pack(side="bottom", fill="x", pady=8)
        ctk.CTkButton(foot, text="⇄  Switch character", anchor="w", height=30,
                      fg_color="transparent",
                      text_color=("gray30", "gray70"),
                      hover_color=("gray80", "gray25"),
                      command=self.switch_character).pack(fill="x", padx=10)
        ctk.CTkButton(foot, text="☾  Toggle theme", anchor="w", height=30,
                      fg_color="transparent",
                      text_color=("gray30", "gray70"),
                      hover_color=("gray80", "gray25"),
                      command=self.toggle_theme).pack(fill="x", padx=10)
        ctk.CTkButton(foot, text="ⓘ  About  ·  v" + APP_VERSION, anchor="w",
                      height=30, fg_color="transparent",
                      text_color=("gray30", "gray70"),
                      hover_color=("gray80", "gray25"),
                      command=self.show_about).pack(fill="x", padx=10)
        self.content = ctk.CTkFrame(body, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True,
                          padx=12, pady=12)
        # sidebar packed only once a save is open (show_page)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=26, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_label = ctk.CTkLabel(
            bar, text="", anchor="w", font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray70"))
        self.status_label.pack(fill="x", padx=16)

    # ---------- page switching ----------
    def _get_page(self, key):
        if key not in self._pages:
            for k, _, module_path, cls_name in PAGES:
                if k == key:
                    try:
                        mod = importlib.import_module(module_path)
                        page_cls = getattr(mod, cls_name)
                    except (ImportError, AttributeError):
                        page_cls = _PlaceholderPage
                    self._pages[key] = page_cls(self.content, self)
                    break
        return self._pages[key]

    def show_page(self, key):
        if self._current is not None:
            self._current.pack_forget()
        if not self.sidebar.winfo_ismapped():
            self.sidebar.pack(side="left", fill="y",
                              before=self.content)
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color=("gray75", "gray28") if k == key
                          else "transparent")
        page = self._get_page(key)
        page.refresh()
        page.pack(fill="both", expand=True)
        self._current = page

    def show_picker(self):
        if self._current is not None:
            self._current.pack_forget()
            self._current = None
        self.sidebar.pack_forget()
        self._update_header()
        picker = self._get_page("picker") if "picker" in self._pages else None
        if picker is None:
            try:
                from ui.pages.picker import PickerPage
                picker = PickerPage(self.content, self)
            except ImportError:
                picker = _PlaceholderPage(self.content, self)
            self._pages["picker"] = picker
        picker.refresh()
        picker.pack(fill="both", expand=True)
        self._current = picker

    # ---------- save flow ----------
    def get_save_dir(self):
        from core import save_locator
        return self.settings.get("save_data_path") or \
            save_locator.default_save_dir()

    def open_save(self, path):
        try:
            self.save = SaveFile.load(path)
        except SaveError as e:
            messagebox.showerror("Cannot open save", str(e))
            return
        self._pages = {k: v for k, v in self._pages.items() if k == "picker"}
        self._update_header()
        self.show_page("overview")
        self.set_status("Loaded {}".format(os.path.basename(path)))

    def do_save(self):
        if not self.save:
            return
        try:
            backup = self.save.save()
        except (SaveError, OSError) as e:
            messagebox.showerror("Save failed", str(e))
            return
        self._update_header()
        if backup:
            self.set_status("Saved. Backup created: {}".format(
                os.path.basename(backup)))
        else:
            self.set_status("Saved.")

    def confirm_discard(self):
        """True when it's OK to drop the current in-memory changes."""
        if not (self.save and self.save.dirty):
            return True
        return messagebox.askyesno(
            "Unsaved changes",
            "You have unsaved changes. Discard them?")

    def switch_character(self):
        if not self.confirm_discard():
            return
        self.save = None
        self.show_picker()

    def on_close(self):
        if self.confirm_discard():
            self.destroy()

    # ---------- shared state helpers (pages call these) ----------
    def mark_dirty(self):
        if self.save:
            self.save.mark_dirty()
        self._update_header()

    def set_status(self, text):
        self.status_label.configure(text=text)

    def _update_header(self):
        if self.save:
            self.header_name.configure(
                text=character.get_name(self.save.data))
            total, _ = skills.summarize(self.save.data)
            self.header_mode.configure(
                text=character.get_mode(self.save.data))
            self.header_level.configure(text="Lv {:,}".format(total))
            self.header_mode.pack(side="left", padx=(0, 4))
            self.header_level.pack(side="left")
            self.save_button.configure(state="normal")
            self.dirty_label.configure(
                text="● unsaved changes" if self.save.dirty else "")
        else:
            self.header_name.configure(text=APP_TITLE)
            self.header_mode.pack_forget()
            self.header_level.pack_forget()
            self.save_button.configure(state="disabled")
            self.dirty_label.configure(text="")

    # ---------- misc ----------
    def toggle_theme(self):
        mode = "light" if ctk.get_appearance_mode().lower() == "dark" \
            else "dark"
        ctk.set_appearance_mode(mode)
        self.settings["theme"] = mode
        config.save_settings(self.settings)

    def show_about(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("About")
        dlg.geometry("460x560")
        dlg.transient(self)
        dlg.grab_set()
        try:
            from PIL import Image
            pil = Image.open(os.path.join(app_root(),
                                          "Dragonwilds_Editor.png"))
            self._about_img = ctk.CTkImage(light_image=pil, dark_image=pil,
                                           size=(96, 96))
            ctk.CTkLabel(dlg, image=self._about_img,
                         text="").pack(pady=(18, 4))
        except Exception:
            pass
        ctk.CTkLabel(dlg, text=APP_TITLE + " v" + APP_VERSION,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
                         pady=(0, 6))
        ctk.CTkLabel(dlg, text=ABOUT_TEXT, justify="left",
                     wraplength=400).pack(padx=24, pady=(4, 8), fill="x")
        ctk.CTkLabel(dlg, text=ABOUT_CREDITS, justify="left",
                     wraplength=400).pack(padx=24, pady=(0, 8),
                                          fill="both", expand=True)
        ctk.CTkButton(dlg, text="Close",
                      command=dlg.destroy).pack(pady=(0, 16))


class _PlaceholderPage(ctk.CTkFrame):
    """Stands in for pages not built yet so the shell always runs."""
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        ctk.CTkLabel(self, text="Coming soon…").pack(expand=True)

    def refresh(self):
        pass
