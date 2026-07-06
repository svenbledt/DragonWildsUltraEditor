"""Save doctor: scans the save for known save-breaking states (dev ids in
unlock lists, invalid mount refs, duplicates) and repairs them."""
import customtkinter as ctk

from core import doctor


class DoctorPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        sf = self.app.save
        if sf is None:
            return
        report = doctor.scan(sf)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(8, 6))
        ctk.CTkLabel(top, text="Save doctor",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(side="left")
        if report:
            ctk.CTkButton(top, text="Fix everything", width=120,
                          command=self._fix_all).pack(side="right")

        if not report:
            card = ctk.CTkFrame(self, corner_radius=10)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text="No problems found ✓",
                         font=ctk.CTkFont(size=14),
                         text_color=("#3a7a3a", "#7ac07a")
                         ).pack(side="left", padx=14, pady=14)
            ctk.CTkLabel(card,
                         text="This save has none of the known "
                              "save-breaking states.",
                         text_color=("gray40", "gray60")).pack(side="left")
            return

        for item in report:
            card = ctk.CTkFrame(self, corner_radius=10)
            card.pack(fill="x", pady=4)
            text = ctk.CTkFrame(card, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True, padx=14, pady=10)
            ctk.CTkLabel(text, text=item["title"], anchor="w",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=("#b04040", "#e08080")).pack(fill="x")
            ctk.CTkLabel(text, text=item["explain"], anchor="w",
                         justify="left", wraplength=520,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray30", "gray70")).pack(fill="x")
            for d in item["details"]:
                ctk.CTkLabel(text, text="• " + d, anchor="w",
                             font=ctk.CTkFont(size=11),
                             text_color=("gray45", "gray55")).pack(fill="x")
            ctk.CTkButton(card, text="Fix", width=80,
                          command=lambda k=item["key"]: self._fix(k)
                          ).pack(side="right", padx=14)

    def _fix(self, key):
        removed = doctor.fix(self.app.save, key)
        self.app.mark_dirty()
        self.app.set_status(
            "Removed {} bad entr{} — press Save to keep.".format(
                removed, "ies" if removed != 1 else "y"))
        self.refresh()

    def _fix_all(self):
        removed = doctor.fix_all(self.app.save)
        self.app.mark_dirty()
        self.app.set_status(
            "Removed {} bad entr{} — press Save to keep.".format(
                removed, "ies" if removed != 1 else "y"))
        self.refresh()
