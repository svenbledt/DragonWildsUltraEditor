"""Storage (PersonalInventory): 20-slot grid (0-19) + storage kits."""
from tkinter import messagebox

import customtkinter as ctk

from core import inventory as inv, presets
from ui.widgets.slot_grid import SlotGrid
from ui.widgets.item_picker import ItemPicker


class StoragePage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(8, 6))
        ctk.CTkLabel(top, text="Storage kit:").pack(side="left")
        self.region_var = ctk.StringVar(value=presets.REGIONS[0])
        self.class_var = ctk.StringVar(value=presets.CLASSES[0])
        ctk.CTkOptionMenu(top, variable=self.region_var, width=150,
                          values=list(presets.REGIONS)).pack(side="left",
                                                             padx=6)
        ctk.CTkOptionMenu(top, variable=self.class_var, width=130,
                          values=list(presets.CLASSES)).pack(side="left")
        ctk.CTkButton(top, text="Apply kit", width=90,
                      command=self._apply_kit).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Clear all", width=90,
                      fg_color="transparent", border_width=1,
                      text_color=("#b04040", "#e08080"),
                      command=self._clear_all).pack(side="right")

        self.grid_widget = SlotGrid(self)
        self.grid_widget.pack(fill="both", expand=True)

    def refresh(self):
        sf = self.app.save
        if sf is None:
            return
        id_to_name, _, _, _ = inv.item_maps()
        lo, hi = inv.STORAGE_RANGE
        self.grid_widget.render(lo, hi, inv.slots(sf, "storage"),
                                id_to_name, self._on_slot,
                                on_hover=self._on_hover)

    def _on_hover(self, slot, name):
        if slot is None:
            self.app.set_status("")
        elif name:
            self.app.set_status("Slot {}: {}".format(slot, name))
        else:
            self.app.set_status("Slot {}: empty — click to add an item"
                                .format(slot))

    def _on_slot(self, slot):
        sf = self.app.save
        current = inv.slots(sf, "storage").get(slot)

        def on_set(item_id, count):
            inv.set_slot(sf, "storage", slot, item_id, count)
            self.app.mark_dirty()
            self.app.set_status(
                "Slot {} updated — press Save to keep.".format(slot))
            self.refresh()

        def on_remove():
            inv.clear_slot(sf, "storage", slot)
            self.app.mark_dirty()
            self.app.set_status(
                "Slot {} cleared — press Save to keep.".format(slot))
            self.refresh()

        ItemPicker(self.app, str(slot), current, on_set, on_remove)

    def _apply_kit(self):
        try:
            key = presets.apply_storage_preset(
                self.app.save, self.region_var.get(), self.class_var.get())
        except ValueError as e:
            self.app.set_status(str(e))
            return
        self.app.mark_dirty()
        self.app.set_status(
            "Applied storage kit {} — press Save to keep.".format(key))
        self.refresh()

    def _clear_all(self):
        if not messagebox.askyesno("Clear all",
                                   "Remove every item from storage?"):
            return
        inv.clear_container(self.app.save, "storage")
        self.app.mark_dirty()
        self.app.set_status("Storage cleared — press Save to keep.")
        self.refresh()
