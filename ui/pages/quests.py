"""Quests: main story / side quests / tutorial tabs, one card per quest
with its state, description, objective progress and rewards. Change the
state per quest, give its rewards, or complete a whole category."""
from tkinter import messagebox

import customtkinter as ctk

from core import inventory as inv, quests
from ui.icons import get_icon

TABS = list(quests.CATEGORY_LABELS)
_STATE_COLORS = {
    quests.STATE_LABELS[quests.STATE_NOT_STARTED]: ("gray40", "gray60"),
    quests.STATE_LABELS[quests.STATE_IN_PROGRESS]: ("#a07020", "#e0b060"),
    quests.READY_LABEL: ("#2060a0", "#70a8e0"),
    quests.STATE_LABELS[quests.STATE_COMPLETED]: ("#3a7a3a", "#7ac07a"),
}
_STATE_CHOICES = list(_STATE_COLORS)


class QuestsPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.category = TABS[0][0]

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(8, 6))
        self.tabs = ctk.CTkSegmentedButton(
            top, values=[label for _, label in TABS], command=self._on_tab)
        self.tabs.set(TABS[0][1])
        self.tabs.pack(side="left")
        self.counter = ctk.CTkLabel(top, text="",
                                    text_color=("gray40", "gray60"))
        self.counter.pack(side="left", padx=12)
        ctk.CTkButton(top, text="Complete all", width=110,
                      command=self._complete_all).pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        sf = self.app.save
        if sf is None:
            return
        states = quests.get_states(sf)
        objectives = quests.get_objectives(sf)
        rows = quests.quests(self.category)
        done = sum(1 for q in rows
                   if states.get(q["quest_id"]) == quests.STATE_COMPLETED)
        self.counter.configure(
            text="{} / {} completed".format(done, len(rows)))
        for q in rows:
            state = states.get(q["quest_id"], quests.STATE_NOT_STARTED)
            self._card(q, quests.display_state(
                q, state, objectives.get(q["quest_id"])))

    def _card(self, q, state):
        card = ctk.CTkFrame(self.list_frame, corner_radius=10)
        card.pack(fill="x", pady=4)

        text = ctk.CTkFrame(card, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, padx=14, pady=10)
        head = ctk.CTkFrame(text, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(head, text=q["name"], anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(side="left")
        ctk.CTkLabel(head, text=state, font=ctk.CTkFont(size=12),
                     text_color=_STATE_COLORS[state]).pack(side="left",
                                                           padx=10)
        if q["description"]:
            ctk.CTkLabel(text, text=q["description"], anchor="w",
                         justify="left", wraplength=520,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray30", "gray70")).pack(fill="x")
        if q["objectives"]:
            ctk.CTkLabel(text,
                         text="{} objectives".format(len(q["objectives"])),
                         anchor="w", font=ctk.CTkFont(size=11),
                         text_color=("gray45", "gray55")).pack(fill="x")
        if q["rewards"]:
            self._rewards_line(text, q)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=14)
        if q["rewards"]:
            ctk.CTkButton(actions, text="Give rewards", width=110,
                          fg_color="transparent", border_width=1,
                          text_color=("gray20", "gray80"),
                          command=lambda: self._give_rewards(q)
                          ).pack(pady=(0, 6))
        var = ctk.StringVar(value=state)
        ctk.CTkOptionMenu(
            actions, variable=var, width=140, values=_STATE_CHOICES,
            command=lambda label, quest=q: self._set_state(
                quest, label)).pack()

    def _rewards_line(self, parent, q):
        line = ctk.CTkFrame(parent, fg_color="transparent")
        line.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(line, text="Rewards:", font=ctk.CTkFont(size=11),
                     text_color=("gray45", "gray55")).pack(side="left")
        id_to_name, _, _, _ = inv.item_maps()
        for r in q["rewards"]:
            name = (id_to_name.get(r["item_id"]) if r["item_id"] else
                    None) or quests.pretty_asset(r["asset"])
            if r["type"] == "recipe_unlock":
                label = "Recipe: {}".format(name)
            elif r["type"] == "mount_unlock":
                label = "Mount: {}".format(quests.pretty_asset(r["asset"]))
            else:
                label = "{}{}".format(
                    name, " x{}".format(r["count"]) if r["count"] > 1
                    else "")
            icon = get_icon(r["item_id"], size=20) if r["item_id"] else None
            ctk.CTkLabel(line, image=icon, text=" " + label, compound="left",
                         font=ctk.CTkFont(size=11)).pack(side="left", padx=6)

    def _on_tab(self, label):
        for key, lab in TABS:
            if lab == label:
                self.category = key
        self.refresh()

    def _set_state(self, q, label):
        if label == quests.READY_LABEL:
            quests.set_ready_to_turn_in(self.app.save, q)
            self.app.set_status(
                "Quest set to its final objective — turn it in at the NPC "
                "to receive the rewards in-game. Press Save to keep.")
        else:
            state = {v: k for k, v in quests.STATE_LABELS.items()}[label]
            quests.set_state(self.app.save, q["quest_id"], state)
            self.app.set_status(
                "Quest set to {} — press Save to keep.".format(label))
        self.app.mark_dirty()
        self.refresh()

    def _give_rewards(self, q):
        granted, skipped = quests.grant_rewards(self.app.save, q)
        if granted:
            self.app.mark_dirty()
        parts = []
        if granted:
            parts.append("Granted: " + ", ".join(granted))
        if skipped:
            parts.append("Skipped: " + ", ".join(skipped)
                         if granted else ", ".join(skipped))
        self.app.set_status(
            ("; ".join(parts) + " — press Save to keep.") if granted
            else ("; ".join(parts) or "This quest has no rewards."))
        self.refresh()

    def _complete_all(self):
        label = dict(TABS)[self.category]
        if not messagebox.askyesno(
                "Complete all",
                "Mark every {} quest as completed?".format(label.lower())):
            return
        changed = quests.complete_all(self.app.save, self.category)
        if changed:
            self.app.mark_dirty()
        self.app.set_status(
            "Marked {} quests completed — press Save to keep. Use each "
            "quest's Give rewards button to also claim rewards.".format(
                changed) if changed else "All quests already completed.")
        self.refresh()
