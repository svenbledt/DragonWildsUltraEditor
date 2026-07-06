"""Launch screen: pick a character save from the game's save folder."""
import datetime
from tkinter import filedialog

import customtkinter as ctk

from core import config, save_locator


def _ago(mtime):
    if not mtime:
        return ""
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(mtime)
    if delta.days > 1:
        return "played {} days ago".format(delta.days)
    if delta.days == 1:
        return "played yesterday"
    hours = delta.seconds // 3600
    if hours:
        return "played {} h ago".format(hours)
    return "played just now"


class PickerPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        folder = self.app.get_save_dir()
        ctk.CTkLabel(self, text="Choose a character",
                     font=ctk.CTkFont(size=20, weight="bold")
                     ).pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(self, text="Looking in  " + folder,
                     text_color=("gray40", "gray60")
                     ).pack(anchor="w", pady=(0, 12))

        chars = save_locator.list_characters(folder)
        if chars:
            lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
            lst.pack(fill="both", expand=True)
            for c in chars:
                card = ctk.CTkFrame(lst, corner_radius=10)
                card.pack(fill="x", pady=4)
                ctk.CTkLabel(card, text=c["name"],
                             font=ctk.CTkFont(size=15, weight="bold")
                             ).pack(anchor="w", padx=14, pady=(10, 0))
                sub = "{}  ·  Total level {:,}  ·  {}".format(
                    c["mode"], c["total_level"], _ago(c["mtime"]))
                ctk.CTkLabel(card, text=sub,
                             text_color=("gray40", "gray60")
                             ).pack(anchor="w", padx=14, pady=(0, 10))
                for w in (card, *card.winfo_children()):
                    w.bind("<Button-1>",
                           lambda _e, p=c["path"]: self.app.open_save(p))
        else:
            ctk.CTkLabel(self, text="No character saves found here.",
                         text_color=("gray40", "gray60")
                         ).pack(anchor="w", pady=12)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=10)
        ctk.CTkButton(row, text="Open a file manually…",
                      command=self._browse).pack(side="left")
        ctk.CTkButton(row, text="Change folder…", fg_color="transparent",
                      border_width=1,
                      text_color=("gray20", "gray80"),
                      command=self._change_folder).pack(side="left", padx=8)

    def _browse(self):
        path = filedialog.askopenfilename(
            initialdir=self.app.get_save_dir(),
            filetypes=[("Dragonwilds saves", "*.json")])
        if path:
            self.app.open_save(path)

    def _change_folder(self):
        folder = filedialog.askdirectory(initialdir=self.app.get_save_dir())
        if folder:
            self.app.settings["save_data_path"] = folder
            config.save_settings(self.app.settings)
            self.refresh()
