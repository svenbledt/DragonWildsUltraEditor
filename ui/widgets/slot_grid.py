"""Game-like grid of item slots, styled after the in-game inventory:
the icon fills the tile, the stack count overlays the bottom-right corner
(only for stacks above 1), and an optional hotbar renders the first row
with slot-number badges and a visual gap, like slots 1-8 in-game.
Click a tile -> on_slot(slot); hovering reports the item via on_hover."""
import customtkinter as ctk

from ui.icons import get_icon

TILE = 84       # tile square, px
ICON = 62       # icon size inside the tile

_FILLED = ("gray85", "gray17")
_FILLED_HOVER = ("gray72", "gray26")
_EMPTY = ("gray92", "gray13")
_EMPTY_HOVER = ("gray82", "gray20")


def short_name(name, limit=22):
    return name if len(name) <= limit else name[:limit - 1] + "…"


class SlotGrid(ctk.CTkScrollableFrame):
    def __init__(self, master, columns=8, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columns = columns

    def render(self, lo, hi, entries, id_to_name, on_slot, hotbar=0,
               on_hover=None):
        """entries: {slot:int -> entry dict} (from core.inventory.slots).
        hotbar: render the first N slots as a separated, numbered row."""
        for w in self.winfo_children():
            w.destroy()
        for i, slot in enumerate(range(lo, hi + 1)):
            badge = str(i + 1) if i < hotbar else None
            tile = self._tile(entries.get(slot), slot, id_to_name,
                              on_slot, badge, on_hover)
            # extra gap under the hotbar row, mirroring the in-game split
            pady = (4, 18) if hotbar and i < self.columns else 4
            tile.grid(row=i // self.columns, column=i % self.columns,
                      padx=4, pady=pady)

    def _tile(self, entry, slot, id_to_name, on_slot, badge, on_hover):
        filled = bool(entry)
        base = _FILLED if filled else _EMPTY
        hover = _FILLED_HOVER if filled else _EMPTY_HOVER
        tile = ctk.CTkFrame(self, width=TILE, height=TILE, corner_radius=8,
                            fg_color=base, border_width=1,
                            border_color=("gray70", "gray26"))
        tile.pack_propagate(False)

        name = ""
        if entry and "ItemData" in entry:
            iid = entry["ItemData"]
            name = id_to_name.get(iid, "?")
            icon = get_icon(iid, size=ICON)
            if icon:
                ctk.CTkLabel(tile, image=icon, text="").place(
                    relx=0.5, rely=0.5, anchor="center")
            else:
                ctk.CTkLabel(tile, text=short_name(name),
                             font=ctk.CTkFont(size=10),
                             wraplength=TILE - 14,
                             text_color=("gray10", "gray90")).place(
                    relx=0.5, rely=0.5, anchor="center")
            count = entry.get("Count", 1)
            if count > 1:
                ctk.CTkLabel(tile, text=" {} ".format(count),
                             font=ctk.CTkFont(size=11, weight="bold"),
                             corner_radius=6, height=18,
                             fg_color=("gray75", "gray10"),
                             text_color=("gray10", "gray95")).place(
                    relx=1.0, rely=1.0, anchor="se", x=-4, y=-4)
        elif entry:   # loadout ref entry (PlayerInventoryItemIndex)
            name = "inventory slot {}".format(
                entry.get("PlayerInventoryItemIndex", "?"))
            ctk.CTkLabel(tile, text="→ {}".format(
                             entry.get("PlayerInventoryItemIndex", "?")),
                         font=ctk.CTkFont(size=11),
                         text_color=("gray40", "gray60")).place(
                relx=0.5, rely=0.5, anchor="center")
        if badge:
            ctk.CTkLabel(tile, text=badge, font=ctk.CTkFont(size=10),
                         text_color=("gray45", "gray55")).place(x=6, y=1)

        def on_enter(_e):
            tile.configure(fg_color=hover)
            if on_hover:
                on_hover(slot, name)

        def on_leave(_e):
            tile.configure(fg_color=base)
            if on_hover:
                on_hover(None, "")

        def on_click(_e):
            on_slot(slot)

        tile.bind("<Enter>", on_enter)
        tile.bind("<Leave>", on_leave)
        for w in (tile, *tile.winfo_children()):
            w.bind("<Button-1>", on_click)
        return tile
