"""Unlocks: one card per category with progress + Unlock all, plus the
map-reveal and status-reset actions."""
from tkinter import messagebox

import customtkinter as ctk

from core import unlocks


class UnlocksPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        sf = self.app.save
        if sf is None:
            return
        for cat in unlocks.categories(sf):
            row = ctk.CTkFrame(self, corner_radius=10)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=cat["label"], width=150, anchor="w",
                         font=ctk.CTkFont(size=14, weight="bold")
                         ).pack(side="left", padx=14, pady=12)
            done = cat["done"]
            ctk.CTkLabel(
                row,
                text="{} / {} unlocked".format(cat["have"], cat["total"]),
                text_color=("#3a7a3a", "#7ac07a") if done
                else ("gray40", "gray60")).pack(side="left")
            ctk.CTkButton(
                row, text="Done ✓" if done else "Unlock all", width=110,
                state="disabled" if done else "normal",
                command=lambda k=cat["key"]: self._unlock(k)
            ).pack(side="right", padx=14)

        extras = ctk.CTkFrame(self, corner_radius=10)
        extras.pack(fill="x", pady=(14, 4))
        ctk.CTkLabel(extras, text="Map & status", width=150, anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(side="left", padx=14, pady=12)
        ctk.CTkButton(extras, text="Reveal whole map", width=140,
                      command=self._reveal).pack(side="right", padx=14)
        ctk.CTkButton(extras, text="Reset health & status", width=160,
                      fg_color="transparent", border_width=1,
                      text_color=("gray20", "gray80"),
                      command=self._reset).pack(side="right")

    def _unlock(self, key):
        try:
            added, total = unlocks.unlock_all(self.app.save, key)
        except ValueError as e:
            self.app.set_status(str(e))
            return
        self.app.mark_dirty()
        self.app.set_status(
            "Unlocked {} new (now {}) — press Save to keep.".format(
                added, total))
        self.refresh()

    def _reveal(self):
        unlocks.reveal_map(self.app.save)
        self.app.mark_dirty()
        self.app.set_status("Map revealed — press Save to keep.")

    def _reset(self):
        if not messagebox.askyesno("Reset health & status",
                                   "Reset health and status effects?"):
            return
        try:
            unlocks.reset_status(self.app.save)
        except ValueError as e:
            self.app.set_status(str(e))
            return
        self.app.mark_dirty()
        self.app.set_status("Health and status reset — press Save to keep.")
