"""Overview: stat cards + one-click quick actions."""
import customtkinter as ctk

from core import character, skills, unlocks


class OverviewPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        sf = self.app.save
        if sf is None:
            return
        total, maxed = skills.summarize(sf.data)
        unlocked_done = sum(1 for c in unlocks.categories(sf) if c["done"])

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", pady=(8, 16))
        stats = [
            ("Total level", "{:,}".format(total)),
            ("Maxed skills", "{} / {}".format(maxed, len(skills.SKILL_IDS))),
            ("Max HP", str(unlocks.computed_max_hp(sf))),
            ("Mode", character.get_mode(sf.data)),
            ("Unlock groups done", "{} / 5".format(unlocked_done)),
        ]
        for title, value in stats:
            card = ctk.CTkFrame(cards, corner_radius=10)
            card.pack(side="left", expand=True, fill="x", padx=4)
            ctk.CTkLabel(card, text=value,
                         font=ctk.CTkFont(size=22, weight="bold")
                         ).pack(pady=(14, 0))
            ctk.CTkLabel(card, text=title,
                         text_color=("gray40", "gray60")
                         ).pack(pady=(0, 14))

        ctk.CTkLabel(self, text="Quick actions",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", pady=(8, 6))
        for label, desc, action in [
            ("Max all skills", "Set every skill to level 99.",
             self._max_skills),
            ("Unlock everything",
             "All recipes, buildings, mounts, urns, compendium and the map.",
             self._unlock_everything),
            ("Reset health & status",
             "Full health, food, water; clears toxins.", self._reset_status),
        ]:
            row = ctk.CTkFrame(self, corner_radius=10)
            row.pack(fill="x", pady=4)
            ctk.CTkButton(row, text=label, width=190, command=action
                          ).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(row, text=desc, text_color=("gray40", "gray60")
                         ).pack(side="left", padx=6)
        ctk.CTkLabel(
            self, text="Changes stay in memory until you press Save.",
            text_color=("gray50", "gray55")).pack(anchor="w", pady=(14, 0))

    def _max_skills(self):
        skills.max_all_skills(self.app.save)
        self.app.mark_dirty()
        self.app.set_status("All skills set to 99 — press Save to keep.")
        self.refresh()

    def _unlock_everything(self):
        sf = self.app.save
        added = 0
        skipped = []
        for cat in unlocks.categories(sf):
            try:
                a, _ = unlocks.unlock_all(sf, cat["key"])
                added += a
            except ValueError:
                skipped.append(cat["label"])
        unlocks.reveal_map(sf)
        self.app.mark_dirty()
        msg = "Unlocked {} new entries and revealed the map".format(added)
        if skipped:
            msg += " (skipped: {})".format(", ".join(skipped))
        self.app.set_status(msg + " — press Save to keep.")
        self.refresh()

    def _reset_status(self):
        try:
            unlocks.reset_status(self.app.save)
        except ValueError as e:
            self.app.set_status(str(e))
            return
        self.app.mark_dirty()
        self.app.set_status("Health and status reset — press Save to keep.")
        self.refresh()
