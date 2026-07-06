"""Game-like grid of item slots. Filled slots show icon (or short name) and
count; empty slots show a dashed +. Click → on_slot(slot)."""
import customtkinter as ctk

from ui.icons import get_icon


def short_name(name, limit=9):
    return name if len(name) <= limit else name[:limit - 1] + "…"


class SlotGrid(ctk.CTkScrollableFrame):
    def __init__(self, master, columns=8, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columns = columns

    def render(self, lo, hi, entries, id_to_name, on_slot):
        """entries: {slot:int -> entry dict} (from core.inventory.slots)."""
        for w in self.winfo_children():
            w.destroy()
        for i, slot in enumerate(range(lo, hi + 1)):
            entry = entries.get(slot)
            if entry and "ItemData" in entry:
                iid = entry["ItemData"]
                name = id_to_name.get(iid, "?")
                icon = get_icon(iid, size=34)
                text = "×{}".format(entry.get("Count", 1)) if icon \
                    else "{}\n×{}".format(short_name(name),
                                          entry.get("Count", 1))
                btn = ctk.CTkButton(
                    self, width=64, height=64, corner_radius=8,
                    image=icon, text=text, compound="top",
                    font=ctk.CTkFont(size=10),
                    fg_color=("gray85", "gray20"),
                    hover_color=("gray75", "gray28"),
                    text_color=("gray10", "gray90"),
                    command=lambda s=slot: on_slot(s))
            elif entry:   # loadout ref entry (PlayerInventoryItemIndex)
                btn = ctk.CTkButton(
                    self, width=64, height=64, corner_radius=8,
                    text="slot {}".format(
                        entry.get("PlayerInventoryItemIndex", "?")),
                    font=ctk.CTkFont(size=10),
                    fg_color=("gray85", "gray20"),
                    hover_color=("gray75", "gray28"),
                    text_color=("gray40", "gray60"),
                    command=lambda s=slot: on_slot(s))
            else:
                btn = ctk.CTkButton(
                    self, width=64, height=64, corner_radius=8, text="+",
                    fg_color="transparent", border_width=1,
                    border_color=("gray70", "gray30"),
                    text_color=("gray50", "gray50"),
                    hover_color=("gray85", "gray22"),
                    command=lambda s=slot: on_slot(s))
            btn.grid(row=i // self.columns, column=i % self.columns,
                     padx=4, pady=4)
