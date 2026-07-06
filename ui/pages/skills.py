"""Skills: one row per skill with linked Level/XP fields."""
import customtkinter as ctk

from core import skills


class SkillsPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._rows = []          # (skill_id, level_var, xp_var)
        self._syncing = False

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._rows = []
        sf = self.app.save
        if sf is None:
            return
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 6))
        ctk.CTkButton(bar, text="Apply skills", width=120,
                      command=self._apply).pack(side="left")
        ctk.CTkButton(bar, text="Max all (99)", width=120,
                      fg_color="transparent", border_width=1,
                      text_color=("gray20", "gray80"),
                      command=self._max_all).pack(side="left", padx=8)

        grid = ctk.CTkScrollableFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        head = ctk.CTkFrame(grid, fg_color="transparent")
        head.pack(fill="x")
        for text, width in (("Skill", 160), ("Level", 80), ("XP", 120)):
            ctk.CTkLabel(head, text=text, width=width, anchor="w",
                         font=ctk.CTkFont(weight="bold")
                         ).pack(side="left", padx=6)
        for row in skills.get_skills(sf):
            self._add_row(grid, row)

    def _add_row(self, parent, row):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        ctk.CTkLabel(frame, text=row["label"], width=160, anchor="w"
                     ).pack(side="left", padx=6)
        level_var = ctk.StringVar(value=str(row["level"]))
        xp_var = ctk.StringVar(value=str(row["xp"]))
        ctk.CTkEntry(frame, textvariable=level_var, width=80
                     ).pack(side="left", padx=6)
        ctk.CTkEntry(frame, textvariable=xp_var, width=120
                     ).pack(side="left", padx=6)
        level_var.trace_add(
            "write", lambda *_: self._sync(level_var, xp_var, "level"))
        xp_var.trace_add(
            "write", lambda *_: self._sync(level_var, xp_var, "xp"))
        self._rows.append((row["id"], level_var, xp_var))

    def _sync(self, level_var, xp_var, source):
        if self._syncing:
            return
        self._syncing = True
        try:
            if source == "level":
                lvl = int(level_var.get())
                xp_var.set(str(skills.get_xp_for_level(lvl)))
            else:
                xp = int(xp_var.get())
                level_var.set(str(skills.get_level_for_xp(xp)))
        except ValueError:
            pass      # mid-typing; leave the counterpart alone
        finally:
            self._syncing = False

    def _apply(self):
        sf = self.app.save
        applied = 0
        for skill_id, _level_var, xp_var in self._rows:
            try:
                xp = min(int(xp_var.get()), skills.MAX_LEVEL_XP)
            except ValueError:
                continue
            skills.set_skill_xp(sf, skill_id, xp)
            applied += 1
        self.app.mark_dirty()
        self.app.set_status(
            "Applied {} skills — press Save to keep.".format(applied))

    def _max_all(self):
        skills.max_all_skills(self.app.save)
        self.app.mark_dirty()
        self.app.set_status("All skills set to 99 — press Save to keep.")
        self.refresh()
