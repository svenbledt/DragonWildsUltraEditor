"""Modal item chooser: search, amount, Set / Remove."""
import customtkinter as ctk

from core import inventory as inv
from ui.icons import get_icon

MAX_RESULTS = 60


class ItemPicker(ctk.CTkToplevel):
    def __init__(self, master, slot_label, current_entry, on_set, on_remove):
        super().__init__(master)
        self.on_set = on_set
        self.on_remove = on_remove
        self.selected_id = (current_entry or {}).get("ItemData")
        self.title("Slot {}".format(slot_label))
        self.geometry("420x520")
        self.transient(master)
        self.grab_set()

        id_to_name, self.name_to_id, _, _ = inv.item_maps()
        self.names = sorted(self.name_to_id)

        self.search_var = ctk.StringVar()
        entry = ctk.CTkEntry(self, textvariable=self.search_var,
                             placeholder_text="Search items…")
        entry.pack(fill="x", padx=14, pady=(14, 8))
        entry.focus_set()
        self.search_var.trace_add("write", lambda *_: self._render_results())

        self.results = ctk.CTkScrollableFrame(self)
        self.results.pack(fill="both", expand=True, padx=14)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(bottom, text="Amount").pack(side="left")
        self.count_var = ctk.StringVar(
            value=str((current_entry or {}).get("Count", 1)))
        ctk.CTkEntry(bottom, textvariable=self.count_var, width=70
                     ).pack(side="left", padx=8)
        ctk.CTkButton(bottom, text="Set", width=90, command=self._set
                      ).pack(side="right")
        if current_entry:
            ctk.CTkButton(bottom, text="Remove", width=90,
                          fg_color="transparent", border_width=1,
                          text_color=("#b04040", "#e08080"),
                          command=self._remove).pack(side="right", padx=8)
        self.hint = ctk.CTkLabel(self, text="",
                                 text_color=("#b04040", "#e08080"))
        self.hint.pack(pady=(0, 8))
        self._render_results()

    def _render_results(self):
        for w in self.results.winfo_children():
            w.destroy()
        query = self.search_var.get().strip().lower()
        shown = 0
        for name in self.names:
            if query and query not in name.lower():
                continue
            iid = self.name_to_id[name]
            selected = iid == self.selected_id
            row = ctk.CTkButton(
                self.results, text=name, anchor="w", height=34,
                image=get_icon(iid, size=24), compound="left",
                fg_color=("gray75", "gray30") if selected else "transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                command=lambda i=iid: self._pick(i))
            row.pack(fill="x", pady=1)
            shown += 1
            if shown >= MAX_RESULTS:
                ctk.CTkLabel(self.results,
                             text="…keep typing to narrow it down",
                             text_color=("gray40", "gray60")).pack(pady=4)
                break

    def _pick(self, item_id):
        self.selected_id = item_id
        self._render_results()

    def _set(self):
        if not self.selected_id:
            self.hint.configure(text="Pick an item first.")
            return
        try:
            count = int(self.count_var.get())
        except ValueError:
            self.hint.configure(text="Amount must be a number.")
            return
        try:
            self.on_set(self.selected_id, count)
        except ValueError as e:
            self.hint.configure(text=str(e))
            return
        self.destroy()

    def _remove(self):
        self.on_remove()
        self.destroy()
