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
_OBJ_DONE_COLOR = ("#3a7a3a", "#7ac07a")
_OBJ_CURRENT_COLOR = ("#a07020", "#e0b060")
_OBJ_PENDING_COLOR = ("gray45", "gray55")


class QuestsPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.category = TABS[0][0]
        self._expanded = set()   # quest_ids with an open objective list

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
            self._card(q, state, objectives.get(q["quest_id"]))

    def _card(self, q, state, objective):
        label = quests.display_state(q, state, objective)
        card = ctk.CTkFrame(self.list_frame, corner_radius=10)
        card.pack(fill="x", pady=4)

        text = ctk.CTkFrame(card, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, padx=14, pady=10)
        head = ctk.CTkFrame(text, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(head, text=q["name"], anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(side="left")
        ctk.CTkLabel(head, text=label, font=ctk.CTkFont(size=12),
                     text_color=_STATE_COLORS[label]).pack(side="left",
                                                           padx=10)
        if q["description"]:
            ctk.CTkLabel(text, text=q["description"], anchor="w",
                         justify="left", wraplength=520,
                         font=ctk.CTkFont(size=12),
                         text_color=("gray30", "gray70")).pack(fill="x")
        if q["objectives"]:
            self._objectives_block(text, q, state, objective)
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
        var = ctk.StringVar(value=label)
        ctk.CTkOptionMenu(
            actions, variable=var, width=140, values=_STATE_CHOICES,
            command=lambda label, quest=q: self._set_state(
                quest, label)).pack()

    def _objectives_block(self, parent, q, state, objective):
        expanded = q["quest_id"] in self._expanded
        toggle = ctk.CTkLabel(
            parent, text="{} Objectives ({})".format(
                "▾" if expanded else "▸", len(q["objectives"])),
            anchor="w", font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"), cursor="hand2")
        toggle.pack(fill="x")
        toggle.bind("<Button-1>",
                    lambda e, qid=q["quest_id"]: self._toggle_objectives(qid))
        if not expanded:
            return
        # ladder position: rows above the current objective are done
        if state == quests.STATE_COMPLETED:
            current = len(q["objectives"])
        elif (state == quests.STATE_IN_PROGRESS
                and objective in q["objectives"]):
            current = q["objectives"].index(objective)
        else:
            current = -1
        for i, obj in enumerate(q["objectives"]):
            if i < current or state == quests.STATE_COMPLETED:
                symbol, color = "✓", _OBJ_DONE_COLOR
            elif i == current:
                symbol, color = "●", _OBJ_CURRENT_COLOR
            else:
                symbol, color = "○", _OBJ_PENDING_COLOR
            row = ctk.CTkLabel(
                parent, text="    {} {}".format(
                    symbol, quests.objective_label(q, obj)),
                anchor="w", justify="left", wraplength=500,
                font=ctk.CTkFont(size=11), text_color=color, cursor="hand2")
            row.pack(fill="x")
            row.bind("<Button-1>", lambda e, quest=q, oid=obj:
                     self._jump_objective(quest, oid))

    def _toggle_objectives(self, quest_id):
        if quest_id in self._expanded:
            self._expanded.discard(quest_id)
        else:
            self._expanded.add(quest_id)
        self.refresh()

    def _jump_objective(self, q, objective_id):
        sf = self.app.save
        # leaving Completed must respect main story order downwards
        if quests.get_states(sf).get(q["quest_id"]) == quests.STATE_COMPLETED:
            blockers = quests.main_story_uncomplete_blockers(sf, q)
            if blockers:
                self.app.set_status(
                    "Blocked: uncomplete {} first (main story order)."
                    .format(", ".join(blockers)))
                return
        # the final objective is 'Ready to turn in' — same forward rule
        if objective_id == quests.final_objective(q):
            blockers = quests.main_story_blockers(sf, q)
            if blockers:
                self.app.set_status(
                    "Blocked: complete {} first (main story order)."
                    .format(", ".join(blockers)))
                return
        notes = quests.set_objective(sf, q, objective_id)
        if objective_id == quests.final_objective(q):
            msg = ("Quest set to its final objective — turn it in at the "
                   "NPC to receive the rewards in-game.")
        else:
            msg = "Quest set to objective: {}.".format(
                quests.objective_label(q, objective_id).rstrip("."))
        self.app.set_status(msg + self._sync_note(notes)
                            + self._rewind_note(q) + " Press Save to keep.")
        self.app.mark_dirty()
        self.refresh()

    def _rewind_note(self, q):
        """Making a main quest the active story point resets later main
        quests that were still running — one active main quest only."""
        names = quests.rewind_later_main_quests(self.app.save, q)
        return (" Also reset the now-out-of-order main quest{}: {}.".format(
            "s" if len(names) != 1 else "", ", ".join(names))
            if names else "")

    @staticmethod
    def _sync_note(notes):
        """Umbral Sands edits keep the camp favour, task quests and main
        quest consistent with each other — tell the user what moved."""
        return (" Synced: {}.".format("; ".join(notes)) if notes else "")

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
        sf = self.app.save
        # main story must be completed in order — a later main quest can't
        # be completed or made turn-in-ready over an incomplete predecessor
        if label in (quests.READY_LABEL,
                     quests.STATE_LABELS[quests.STATE_COMPLETED]):
            blockers = quests.main_story_blockers(sf, q)
            if blockers:
                self.app.set_status(
                    "Blocked: complete {} first (main story order)."
                    .format(", ".join(blockers)))
                self.refresh()
                return
        # ...and uncompleted in reverse order — an earlier main quest can't
        # be downgraded while a later one is still Completed
        else:
            if (quests.get_states(sf).get(q["quest_id"])
                    == quests.STATE_COMPLETED):
                blockers = quests.main_story_uncomplete_blockers(sf, q)
                if blockers:
                    self.app.set_status(
                        "Blocked: uncomplete {} first (main story order)."
                        .format(", ".join(blockers)))
                    self.refresh()
                    return
        notes = []
        if label == quests.READY_LABEL:
            notes = quests.set_ready_to_turn_in(sf, q)
            msg = ("Quest set to its final objective — turn it in at the "
                   "NPC to receive the rewards in-game.")
        elif label == quests.STATE_LABELS[quests.STATE_NOT_STARTED]:
            quests.reset_quest(sf, q["quest_id"])
            msg = "Quest reset to Not started."
        elif label == quests.STATE_LABELS[quests.STATE_IN_PROGRESS]:
            notes = quests.set_in_progress(sf, q)
            msg = "Quest set to In progress."
        else:
            notes = quests.set_state(sf, q["quest_id"],
                                     quests.STATE_COMPLETED)
            msg = "Quest set to Completed."
        msg += self._sync_note(notes)
        if label != quests.STATE_LABELS[quests.STATE_COMPLETED]:
            msg += self._rewind_note(q)
        self.app.set_status(msg + " Press Save to keep.")
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
