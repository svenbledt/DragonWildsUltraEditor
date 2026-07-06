"""Inventory: tab chips (Bag/Runes/Ammo/Quest/Loadout) over the slot grid,
plus gear-kit presets and Clear all."""
from tkinter import messagebox

import customtkinter as ctk

from core import inventory as inv, presets
from ui.widgets.slot_grid import SlotGrid
from ui.widgets.item_picker import ItemPicker

TABS = [label for label, _, _ in inv.INVENTORY_TABS] + ["Loadout"]


class InventoryPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.tab = "Bag"

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(8, 6))
        self.tabs = ctk.CTkSegmentedButton(
            top, values=TABS, command=self._on_tab)
        self.tabs.set(self.tab)
        self.tabs.pack(side="left")
        ctk.CTkButton(top, text="Clear all", width=90,
                      fg_color="transparent", border_width=1,
                      text_color=("#b04040", "#e08080"),
                      command=self._clear_all).pack(side="right")

        kit = ctk.CTkFrame(self, fg_color="transparent")
        kit.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(kit, text="Gear kit:").pack(side="left")
        self.region_var = ctk.StringVar(value=presets.REGIONS[0])
        self.class_var = ctk.StringVar(value=presets.CLASSES[0])
        ctk.CTkOptionMenu(kit, variable=self.region_var, width=150,
                          values=list(presets.REGIONS)).pack(side="left",
                                                             padx=6)
        ctk.CTkOptionMenu(kit, variable=self.class_var, width=130,
                          values=list(presets.CLASSES)).pack(side="left")
        ctk.CTkButton(kit, text="Apply kit", width=90,
                      command=self._apply_kit).pack(side="left", padx=8)

        self.grid_widget = SlotGrid(self)
        self.grid_widget.pack(fill="both", expand=True)

    def refresh(self):
        sf = self.app.save
        if sf is None:
            return
        id_to_name, _, _, _ = inv.item_maps()
        if self.tab == "Loadout":
            entries = inv.slots(sf, "loadout")
            hi = max(entries) if entries else 11
            self.grid_widget.render(0, max(hi, 11), entries, id_to_name,
                                    self._on_slot)
        else:
            lo, hi = inv.slot_bounds("inventory", self.tab)
            self.grid_widget.render(lo, hi, inv.slots(sf, "inventory"),
                                    id_to_name, self._on_slot)

    def _container(self):
        return "loadout" if self.tab == "Loadout" else "inventory"

    def _on_tab(self, value):
        self.tab = value
        self.refresh()

    def _on_slot(self, slot):
        sf = self.app.save
        name = self._container()
        current = inv.slots(sf, name).get(slot)

        def on_set(item_id, count):
            inv.set_slot(sf, name, slot, item_id, count)
            self.app.mark_dirty()
            self.app.set_status(
                "Slot {} updated — press Save to keep.".format(slot))
            self.refresh()

        def on_remove():
            inv.clear_slot(sf, name, slot)
            self.app.mark_dirty()
            self.app.set_status(
                "Slot {} cleared — press Save to keep.".format(slot))
            self.refresh()

        ItemPicker(self.app, str(slot), current, on_set, on_remove)

    def _apply_kit(self):
        try:
            key = presets.apply_gear_preset(
                self.app.save, self.region_var.get(), self.class_var.get())
        except ValueError as e:
            self.app.set_status(str(e))
            return
        self.app.mark_dirty()
        self.app.set_status(
            "Applied gear kit {} — press Save to keep.".format(key))
        self.refresh()

    def _clear_all(self):
        name = self._container()
        if not messagebox.askyesno(
                "Clear all",
                "Remove every item from {}?".format(
                    "the loadout" if name == "loadout" else "the inventory")):
            return
        inv.clear_container(self.app.save, name)
        self.app.mark_dirty()
        self.app.set_status("Cleared — press Save to keep.")
        self.refresh()
