import tkinter as tk
from tkinter import ttk, messagebox
import os
from collections import OrderedDict
import base64

# === LOAD ITEM LIST FROM PYTHON FILE ===
from item_ids import ITEM_LIST

# Region x class best-in-slot gear templates (5 regions x Melee/Ranged/Magic).
# Defined once in loadout_presets.py so the gear and storage tabs stay in sync.
from loadout_presets import (
    GEAR_LOADOUTS, REGIONS, CLASSES, preset_key,
    RUNE_TAB, AMMO_TAB, QUEST_TAB,
)

# Shared item-map builder that disambiguates duplicate names (e.g. the 4
# Ascension Core power levels) so every catalog record is selectable.
from item_maps import build_item_maps

def generate_guid():
    return base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8').rstrip('=')

def fix_max_slot_index(inventory):
    slot_keys = [int(k) for k in inventory.keys() if k.isdigit()]
    max_slot = max(slot_keys) if slot_keys else -1
    items_part = [(k, v) for k, v in inventory.items() if k != "MaxSlotIndex"]
    fixed = OrderedDict(sorted(items_part, key=lambda x: int(x[0]) if x[0].isdigit() else -1))
    fixed["MaxSlotIndex"] = max_slot
    inventory.clear()
    inventory.update(fixed)

def is_rune_or_quest_slot(idx):
    # Real tab layout (verified from saves): Runes 32-55, Ammo 56-79, Quest 80-103.
    idx = int(idx)
    return (32 <= idx <= 55 or 56 <= idx <= 79 or 80 <= idx <= 103)

def setup_editor_tab(
    tab,
    data,
    refresh_json_preview,
    save_json_func,
    refresh_inventory_and_storage=None,
    inv_slot_count=80,
    inv_slot_start=0,
    inv_slot_end=79
):
    if data is None:
        data = {}

    # === LOAD ITEM LIST HERE ===
    items = ITEM_LIST
    id_to_name, name_to_id, id_to_guids, id_to_extra = build_item_maps(items)
    all_item_names = sorted(name_to_id.keys())
    item_names = ["Empty"] + all_item_names

    for w in tab.winfo_children():
        w.destroy()

    if "Inventory" not in data or not isinstance(data["Inventory"], OrderedDict):
        if "Inventory" in data and isinstance(data["Inventory"], dict):
            old_inv = data["Inventory"]
            inv_items = [(k, old_inv[k]) for k in sorted(old_inv, key=lambda x: int(x) if x.isdigit() else 10**6)]
            data["Inventory"] = OrderedDict(inv_items)
        else:
            data["Inventory"] = OrderedDict()
    inventory = data["Inventory"]
    if "Loadout" not in data or not isinstance(data["Loadout"], OrderedDict):
        if "Loadout" in data and isinstance(data["Loadout"], dict):
            old_ld = data["Loadout"]
            ld_items = [(k, old_ld[k]) for k in sorted(old_ld, key=lambda x: int(x) if x.isdigit() else 10**6)]
            data["Loadout"] = OrderedDict(ld_items)
        else:
            data["Loadout"] = OrderedDict()
    loadout = data["Loadout"]

    main_frame = tk.Frame(tab)
    main_frame.pack(fill="both", expand=True)
    left_frame = tk.Frame(main_frame)
    left_frame.pack(side="left", fill="y", padx=16, pady=16, anchor="n")

    # GEAR PRESET SELECT - pick Region (expansion) + combat Class
    tk.Label(left_frame, text="Gear Loadouts (Region + Class)", font=("Arial", 12, "bold")).pack(pady=(0,8))
    tk.Label(
        left_frame,
        text="Best-in-slot kit per region + combat style",
        font=("Arial", 8), fg="#555"
    ).pack(anchor="w", pady=(0, 4))
    preset_frame = tk.Frame(left_frame)
    preset_frame.pack(anchor="w")
    tk.Label(preset_frame, text="Region:").grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
    gear_region_var = tk.StringVar(value=REGIONS[0])
    gear_region_dropdown = ttk.Combobox(
        preset_frame, textvariable=gear_region_var, values=REGIONS, state="readonly", width=16
    )
    gear_region_dropdown.grid(row=0, column=1, sticky="w", pady=2)
    tk.Label(preset_frame, text="Class:").grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
    gear_class_var = tk.StringVar(value=CLASSES[0])
    gear_class_dropdown = ttk.Combobox(
        preset_frame, textvariable=gear_class_var, values=CLASSES, state="readonly", width=16
    )
    gear_class_dropdown.grid(row=1, column=1, sticky="w", pady=2)
    def guidify_dict(d):
        out = OrderedDict()
        for k, v in d.items():
            if isinstance(v, dict):
                entry = dict(v)
                if "PlayerInventoryItemIndex" not in entry and k != "MaxSlotIndex":
                    entry["GUID"] = generate_guid()
                out[k] = entry
            else:
                out[k] = v
        return out
    def apply_gear_loadout():
        preset_name = preset_key(gear_region_var.get(), gear_class_var.get())
        gear = GEAR_LOADOUTS.get(preset_name)
        if not gear:
            messagebox.showerror("Error", f"No gear loadout for '{preset_name}'.")
            return
        new_inv = guidify_dict(gear["Inventory"])
        # Preserve the player's Runes (32-55), Ammo (56-79) and Quest (80-103)
        # items: copy every existing slot in those tabs that the template did
        # NOT fill, so applying a gear loadout never deletes them. The template
        # still wins per-slot, so Magic can place its runes and Ranged its ammo.
        old_inv = data.get("Inventory", {})
        if isinstance(old_inv, dict):
            for k, v in old_inv.items():
                if not (isinstance(k, str) and k.isdigit()):
                    continue
                idx = int(k)
                in_protected = (
                    RUNE_TAB[0] <= idx <= RUNE_TAB[1]
                    or AMMO_TAB[0] <= idx <= AMMO_TAB[1]
                    or QUEST_TAB[0] <= idx <= QUEST_TAB[1]
                )
                if in_protected and k not in new_inv:
                    new_inv[k] = v
        data["Inventory"] = new_inv
        data["Loadout"] = guidify_dict(gear["Loadout"])
        fix_max_slot_index(data["Inventory"])
        fix_max_slot_index(data["Loadout"])
        save_json_func(data)
        refresh_json_preview()
        if refresh_inventory_and_storage:
            refresh_inventory_and_storage()
        update_your_items()
        update_loadout_items()
        try:
            messagebox.showinfo("Success", f"{preset_name} gear loadout applied.")
        except Exception:
            pass
    ttk.Button(preset_frame, text="Apply", command=apply_gear_loadout, width=10).grid(
        row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

    # Add/Update Inventory Slot
    tk.Label(left_frame, text="Add/Update Inventory Slot", font=("Arial", 11, "bold")).pack(pady=(18,0), anchor="w")
    # Slot and Amount fields side-by-side, right above Set Slot button
    slot_amount_frame = tk.Frame(left_frame)
    slot_amount_frame.pack(anchor="w", pady=(4, 0))
    tk.Label(slot_amount_frame, text="Slot:").pack(side="left")
    slot_var = tk.StringVar(value="0")
    slot_options = [str(i) for i in range(inv_slot_start, inv_slot_end + 1)]
    slot_combo = ttk.Combobox(slot_amount_frame, textvariable=slot_var, values=slot_options, width=6, state="readonly")
    slot_combo.pack(side="left", padx=(5, 9))
    tk.Label(slot_amount_frame, text="Amount:").pack(side="left")
    count_var = tk.StringVar(value="1")
    count_entry = tk.Entry(slot_amount_frame, textvariable=count_var, width=8)
    count_entry.pack(side="left", padx=(2, 0))

    # Filterable item list - Filter ABOVE ComboBox now
    filter_item_frame = tk.Frame(left_frame)
    filter_item_frame.pack(anchor="w", fill="x", pady=(8, 0))
    tk.Label(filter_item_frame, text="Filter:", anchor="w").pack(side="top", anchor="w")
    item_search_var = tk.StringVar()
    search_entry = tk.Entry(filter_item_frame, textvariable=item_search_var, width=22)
    search_entry.pack(side="top", anchor="w", pady=(0, 2))
    tk.Label(left_frame, text="Item:").pack(anchor="w")
    item_var = tk.StringVar(value="Empty")
    filtered_item_names = ["Empty"] + all_item_names.copy()
    def update_combobox_list(event=None):
        filter_text = item_search_var.get().lower()
        if filter_text == "":
            filtered = all_item_names
        else:
            filtered = [name for name in all_item_names if filter_text in name.lower()]
        filtered_item_names.clear()
        filtered_item_names.extend(["Empty"] + filtered)
        item_combo["values"] = filtered_item_names
        if item_var.get() not in filtered_item_names:
            item_var.set("Empty")
    search_entry.bind("<KeyRelease>", update_combobox_list)
    search_entry.bind("<FocusIn>", update_combobox_list)
    item_combo = ttk.Combobox(left_frame, textvariable=item_var, values=filtered_item_names, width=30, state="readonly")
    item_combo.pack(anchor="w")

    def find_item_id(item_name):
        return name_to_id.get(item_name.strip())
    def get_extra_for_pid(pid):
        return id_to_extra.get(pid, {})
    def save_and_refresh():
        refresh_json_preview()
        save_json_func(data)
    def add_inventory_item(data, slot_index, item_id, count):
        slot_key = str(slot_index)
        guid = generate_guid()
        extra = get_extra_for_pid(item_id)
        entry = {
            "GUID": guid,
            "ItemData": item_id,
            "Count": count
        }
        if "Durability" in extra:
            entry["Durability"] = extra["Durability"]
        if "VitalShield" in extra:
            entry["VitalShield"] = extra["VitalShield"]
        inventory[slot_key] = entry
        fix_max_slot_index(inventory)
    def remove_inventory_slot(slot_key):
        if slot_key in inventory:
            del inventory[slot_key]
            fix_max_slot_index(inventory)
    def add_update_slot():
        slot = slot_var.get()
        item_name = item_var.get()
        count_text = count_var.get()
        try:
            slot_index = int(slot)
            if slot_index < inv_slot_start or slot_index > inv_slot_end:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", f"Slot must be an integer between {inv_slot_start} and {inv_slot_end}")
            return
        slot_key = str(slot_index)
        if item_name == "Empty":
            remove_inventory_slot(slot_key)
            save_and_refresh()
            update_your_items()
            return
        try:
            count = int(count_text)
            if count < 1:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", f"Invalid count: '{count_text}' (must be a positive integer)")
            return
        item_id = find_item_id(item_name)
        if not item_id:
            messagebox.showerror("Error", f"Item not found: '{item_name}'.")
            return
        add_inventory_item(data, slot_index, item_id, count)
        save_and_refresh()
        update_your_items()
    tk.Button(left_frame, text="Set Slot", command=add_update_slot, width=20).pack(pady=12)

    # BULK ADD (no slot selection, always over main slots only)
    bulk_frame = tk.Frame(left_frame)
    bulk_frame.pack(anchor="w", fill="x", pady=(20, 0))
    tk.Label(bulk_frame, text="Bulk Set Inventory", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 4))

    # Filter row (on its own line)
    filter_row = tk.Frame(bulk_frame)
    filter_row.pack(anchor="w", fill="x")
    tk.Label(filter_row, text="Filter:").pack(side="left")
    bulk_filter_var = tk.StringVar()
    bulk_filter_entry = tk.Entry(filter_row, textvariable=bulk_filter_var, width=24)
    bulk_filter_entry.pack(side="left", padx=(4, 0))

    # Item row (on its own line)
    item_row = tk.Frame(bulk_frame)
    item_row.pack(anchor="w", fill="x", pady=(4, 0))
    tk.Label(item_row, text="Item:").pack(side="left")
    bulk_item_var = tk.StringVar(value="Empty")
    filtered_bulk_item_names = ["Empty"] + all_item_names.copy()
    bulk_item_combo = ttk.Combobox(item_row, textvariable=bulk_item_var, values=filtered_bulk_item_names, width=28, state="readonly")
    bulk_item_combo.pack(side="left", padx=(4,0))

    # Amount row (on its own line)
    amount_row = tk.Frame(bulk_frame)
    amount_row.pack(anchor="w", fill="x", pady=(4, 0))
    tk.Label(amount_row, text="Amount:").pack(side="left")
    bulk_count_var = tk.StringVar(value="1")
    bulk_count_entry = tk.Entry(amount_row, textvariable=bulk_count_var, width=10)
    bulk_count_entry.pack(side="left", padx=(4, 0))

    def update_bulk_item_list(event=None):
        filter_text = bulk_filter_var.get().lower()
        if filter_text == "":
            filtered = all_item_names
        else:
            filtered = [name for name in all_item_names if filter_text in name.lower()]
        filtered_bulk_item_names.clear()
        filtered_bulk_item_names.extend(["Empty"] + filtered)
        bulk_item_combo["values"] = filtered_bulk_item_names
        if bulk_item_var.get() not in filtered_bulk_item_names:
            bulk_item_var.set("Empty")
    bulk_filter_entry.bind("<KeyRelease>", update_bulk_item_list)
    bulk_filter_entry.bind("<FocusIn>", update_bulk_item_list)
    def bulk_apply():
        item_name = bulk_item_var.get()
        count_text = bulk_count_var.get()

        if item_name == "Empty":
            messagebox.showerror("Error", "Bulk: Please select an item.")
            return

        try:
            count = int(count_text)
            if count < 1:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", f"Bulk: Invalid count '{count_text}'")
            return

        item_id = find_item_id(item_name)
        if not item_id:
            messagebox.showerror("Error", f"Bulk: Item not found '{item_name}'")
            return

        is_rune = "rune" in item_name.lower()

        if is_rune:
            # ONLY rune slots 32-55
            target_slots = range(32, 56)
        else:
            # Main slots only
            target_slots = list(range(0, 8)) + list(range(8, 32))

        for idx in target_slots:
            add_inventory_item(data, idx, item_id, count)

        save_and_refresh()
        update_your_items()
    tk.Button(bulk_frame, text="Apply to Main Slots", command=bulk_apply, width=24).pack(pady=8)

    # BULK INFO AT BOTTOM LEFT
    bulk_info_frame = tk.Frame(left_frame)
    bulk_info_frame.pack(side="bottom", fill="x", pady=(20, 0), anchor="s")
    tk.Label(
        bulk_info_frame,
        text=(
            "Slots 0-7 are your Action Bar Slots\n"
            "Slots 8-31 are your Main Inventory Slots\n"
            "Slots 32-55 are your Rune Inventory Slots\n"
            "Slots 56-79 are your Ammo Inventory Slots\n"
            "Slots 80-103 are your Quest Inventory slots"
        ),
        justify="left",
        anchor="w"
    ).pack(anchor="w")

    # INVENTORY LIST
    right_frame = tk.Frame(main_frame)
    right_frame.pack(side="left", fill="both", expand=True, padx=16, pady=16)
    header_frame = tk.Frame(right_frame)
    header_frame.pack(fill="x", pady=(0, 8), padx=4)

    tk.Label(header_frame, text="Your Inventory:", font=("Arial", 12, "bold")).pack(side="left", anchor="w")

    def remove_all_inventory():
        if not messagebox.askyesno("Remove All", "Remove every item from inventory?"):
            return

        # Clear all inventory items
        keys_to_remove = [k for k in inventory.keys() if k != "MaxSlotIndex"]
        for key in keys_to_remove:
            del inventory[key]

        fix_max_slot_index(inventory)

        # Also remove any loadout entries that reference inventory slots,
        # otherwise the save can contain broken dangling references.
        loadout_keys_to_remove = []
        for key, entry in list(loadout.items()):
            if key == "MaxSlotIndex":
                continue
            if isinstance(entry, dict) and "PlayerInventoryItemIndex" in entry:
                loadout_keys_to_remove.append(key)

        for key in loadout_keys_to_remove:
            del loadout[key]

        fix_max_slot_index(loadout)

        save_json_func(data)
        refresh_json_preview()
        update_your_items()
        update_loadout_items()

    tk.Button(
        header_frame,
        text="Remove All",
        command=remove_all_inventory,
        width=12
    ).pack(side="right")
    items_list_frame = tk.Frame(right_frame, borderwidth=1, relief="sunken")
    items_list_frame.pack(fill="both", expand=True, padx=4, pady=(0,10))
    items_canvas = tk.Canvas(items_list_frame, borderwidth=0)
    items_scrollbar = ttk.Scrollbar(items_list_frame, orient="vertical", command=items_canvas.yview)
    items_inner_frame = tk.Frame(items_canvas)
    items_inner_frame.bind(
        "<Configure>",
        lambda e: items_canvas.configure(scrollregion=items_canvas.bbox("all"))
    )
    items_canvas.create_window((0, 0), window=items_inner_frame, anchor="nw")
    items_canvas.configure(yscrollcommand=items_scrollbar.set)
    items_canvas.pack(side="left", fill="both", expand=True)
    items_scrollbar.pack(side="right", fill="y")
    def update_your_items():
        for w in items_inner_frame.winfo_children():
            w.destroy()
        shown = False
        valid_slots = []
        for idx in inventory:
            if idx == "MaxSlotIndex":
                continue
            try:
                i = int(idx)
                valid_slots.append((i, idx))
            except Exception:
                continue
        valid_slots.sort()
        for i, idx in valid_slots:
            entry = inventory[idx]
            item_id = entry.get("ItemData", None)
            count = entry.get("Count", 1)
            item_name = id_to_name.get(item_id, f"Unknown ({item_id})")
            guid = entry.get("GUID", "")
            durability = entry.get("Durability", None)
            vital_shield = entry.get("VitalShield", None)
            row = tk.Frame(items_inner_frame)
            row.pack(fill="x", padx=2, pady=1)
            slot_info = f"Slot {idx} (x{count})"
            tk.Label(row, text=slot_info, width=18, anchor="w").pack(side="left")
            tk.Label(row, text=f"{item_name}", width=28, anchor="w").pack(side="left")
            def clear_slot_closure(idx=idx):
                if idx in inventory:
                    del inventory[idx]
                    fix_max_slot_index(inventory)
                save_json_func(data)
                refresh_json_preview()
                update_your_items()
            tk.Button(row, text="Remove", command=clear_slot_closure, width=8).pack(side="left", padx=(2,2))
            tk.Label(row, text=f"{guid}", width=26, anchor="w").pack(side="left")
            extras = []
            if durability is not None:
                extras.append(f"Dur: {durability}")
            if vital_shield is not None:
                extras.append(f"Shield: {vital_shield}")
            tk.Label(row, text=" | ".join(extras), width=18, anchor="w").pack(side="left")
            shown = True
        if not shown:
            tk.Label(items_inner_frame, text="No items in inventory.").pack(anchor="w", padx=4, pady=8)

    # LOADOUT LIST
    loadout_header_frame = tk.Frame(right_frame)
    loadout_header_frame.pack(fill="x", pady=(14, 8), padx=4)

    tk.Label(
        loadout_header_frame,
        text="Your Loadout:",
        font=("Arial", 12, "bold")
    ).pack(side="left", anchor="w")

    def remove_all_loadout():
        if not messagebox.askyesno("Remove All", "Remove every item from loadout?"):
            return

        keys_to_remove = [k for k in loadout.keys() if k != "MaxSlotIndex"]
        for key in keys_to_remove:
            del loadout[key]

        fix_max_slot_index(loadout)
        save_json_func(data)
        refresh_json_preview()
        update_loadout_items()

    tk.Button(
        loadout_header_frame,
        text="Remove All",
        command=remove_all_loadout,
        width=12
    ).pack(side="right")
    loadout_list_frame = tk.Frame(right_frame, borderwidth=1, relief="sunken")
    loadout_list_frame.pack(fill="both", expand=True, padx=4, pady=(0,10))
    loadout_canvas = tk.Canvas(loadout_list_frame, borderwidth=0)
    loadout_scrollbar = ttk.Scrollbar(loadout_list_frame, orient="vertical", command=loadout_canvas.yview)
    loadout_inner_frame = tk.Frame(loadout_canvas)
    loadout_inner_frame.bind(
        "<Configure>",
        lambda e: loadout_canvas.configure(scrollregion=loadout_canvas.bbox("all"))
    )
    loadout_canvas.create_window((0, 0), window=loadout_inner_frame, anchor="nw")
    loadout_canvas.configure(yscrollcommand=loadout_scrollbar.set)
    loadout_canvas.pack(side="left", fill="both", expand=True)
    loadout_scrollbar.pack(side="right", fill="y")
    def update_loadout_items():
        for w in loadout_inner_frame.winfo_children():
            w.destroy()
        shown = False
        valid_slots = []
        for idx in loadout:
            if idx == "MaxSlotIndex":
                continue
            try:
                i = int(idx)
                valid_slots.append((i, idx))
            except Exception:
                continue
        valid_slots.sort()
        for i, idx in valid_slots:
            entry = loadout[idx]
            if "PlayerInventoryItemIndex" in entry:
                row = tk.Frame(loadout_inner_frame)
                row.pack(fill="x", padx=2, pady=1)
                tk.Label(row, text=f"Slot {idx}", width=7, anchor="w").pack(side="left")
                tk.Label(row, text=f"Ref Inv Slot {entry['PlayerInventoryItemIndex']}", width=30, anchor="w", fg="#0a0").pack(side="left")
                continue
            item_id = entry.get("ItemData", None)
            count = entry.get("Count", 1)
            item_name = id_to_name.get(item_id, f"Unknown ({item_id})")
            guid = entry.get("GUID", "")
            durability = entry.get("Durability", None)
            vital_shield = entry.get("VitalShield", None)
            row = tk.Frame(loadout_inner_frame)
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=f"Slot {idx}", width=7, anchor="w").pack(side="left")
            tk.Label(row, text=f"{item_name}", width=22, anchor="w").pack(side="left")
            tk.Label(row, text=f"x{count}", width=7, anchor="w").pack(side="left")
            tk.Label(row, text=f"{guid}", width=26, anchor="w").pack(side="left")
            extras = []
            if durability is not None:
                extras.append(f"Dur: {durability}")
            if vital_shield is not None:
                extras.append(f"Shield: {vital_shield}")
            tk.Label(row, text=" | ".join(extras), width=18, anchor="w").pack(side="left")
            shown = True
        if not shown:
            tk.Label(loadout_inner_frame, text="No items in loadout.").pack(anchor="w", padx=4, pady=8)

    update_your_items()
    update_loadout_items()