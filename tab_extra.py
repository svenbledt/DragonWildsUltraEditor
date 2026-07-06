import tkinter as tk
from tkinter import ttk, messagebox

import unlock_ops
from data.pickup_ids import EMBEDDED_ITEM_PICKUP_IDS
from data.shrine_ids import EMBEDDED_SHRINE_IDS
from data.unlock_ids import EMBEDDED_RECIPE_IDS, EMBEDDED_BUILDING_IDS, EMBEDDED_MOUNT_TAGS

def setup_extra_tab(tab, data, refresh_preview, save_json_func):
    for widget in tab.winfo_children():
        widget.destroy()

    # --- Map Reveal Section ---
    map_frame = ttk.LabelFrame(tab, text="Reveal Map")
    map_frame.pack(fill="x", padx=10, pady=(10, 0))

    def reveal_map():
        data["RevealedFog"] = {
            "RevealedRegionsBitmap": 4294967295,
            "RevealedRegionsDetectionActive": True
        }
        save_json_func(data)
        refresh_preview()
        messagebox.showinfo("Reveal Map", "The entire map has been revealed.")

    ttk.Button(map_frame, text="Apply", command=reveal_map).pack(side="left", padx=8, pady=7)

    # --- Unlock Recipes Section ---
    recipes_frame = ttk.LabelFrame(tab, text="Unlock Recipes")
    recipes_frame.pack(fill="x", padx=10, pady=(10, 0))

    def recipes_fully_unlocked():
        # data can be None at startup (no save loaded yet); this runs at setup
        # time for the gray-out check, so guard it.
        if not isinstance(data, dict):
            return False
        progress = data.get("Progress")
        if not isinstance(progress, dict):
            return False
        have_r = set(progress.get("RecipesUnlocked") or [])
        return set(EMBEDDED_RECIPE_IDS).issubset(have_r)

    def unlock_recipes():
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Load a save first.")
            return
        progress = data.setdefault("Progress", {})

        # Merge (union) rather than overwrite: a well-progressed save can already
        # contain recipes the embedded snapshot lacks (e.g. new update content).
        # Overwriting would DELETE those. Union only ever adds.
        def merge(key, ids):
            current = progress.get(key)
            current = current if isinstance(current, list) else []
            seen = set(current)
            added = 0
            for i in ids:
                if i not in seen:
                    current.append(i)
                    seen.add(i)
                    added += 1
            progress[key] = current
            return added

        # Only touch the recipe lists. ItemsPickedUp (the item compendium) is a
        # separate, strict-mode-validated list and is NOT needed to craft, so we
        # deliberately leave it alone to avoid an unrelated corruption vector.
        r_added = merge("RecipesUnlocked", EMBEDDED_RECIPE_IDS)
        merge("RecipesNew", EMBEDDED_RECIPE_IDS)

        save_json_func(data)
        refresh_preview()
        recipes_button.config(state="disabled", text="All recipes unlocked")
        messagebox.showinfo(
            "Recipes",
            f"Added {r_added} new recipes (existing entries kept). "
            f"Total: {len(progress['RecipesUnlocked'])} recipes unlocked."
        )

    recipes_button = ttk.Button(
        recipes_frame, text=f"Unlock all recipes ({len(EMBEDDED_RECIPE_IDS)})",
        command=unlock_recipes)
    recipes_button.pack(side="left", padx=8, pady=7)
    if recipes_fully_unlocked():
        recipes_button.config(state="disabled", text="All recipes unlocked")

    # --- Unlock Buildings Section ---
    # Build pieces are unlocked via Progress.BuildingsUnlocked - a SEPARATE id
    # namespace from recipes. Same strict-mode rules apply: an unrecognized id
    # corrupts the save, so EMBEDDED_BUILDING_IDS is a confirmed/folder-filtered
    # list (see build_building_ids.py). Mirrors the recipe unlock exactly.
    buildings_frame = ttk.LabelFrame(tab, text="Unlock Buildings")
    buildings_frame.pack(fill="x", padx=10, pady=(10, 0))

    def buildings_fully_unlocked():
        if not isinstance(data, dict):
            return False
        progress = data.get("Progress")
        if not isinstance(progress, dict):
            return False
        have_b = set(progress.get("BuildingsUnlocked") or [])
        return set(EMBEDDED_BUILDING_IDS).issubset(have_b)

    def unlock_buildings():
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Load a save first.")
            return
        progress = data.setdefault("Progress", {})

        # Union, never overwrite (a save may hold buildings the snapshot lacks).
        def merge(key, ids):
            current = progress.get(key)
            current = current if isinstance(current, list) else []
            seen = set(current)
            added = 0
            for i in ids:
                if i not in seen:
                    current.append(i)
                    seen.add(i)
                    added += 1
            progress[key] = current
            return added

        b_added = merge("BuildingsUnlocked", EMBEDDED_BUILDING_IDS)
        # BuildingPiecesNew is the buildings analogue of RecipesNew (the "new!"
        # badge list); mirror recipes and mark the freshly-unlocked ones.
        merge("BuildingPiecesNew", EMBEDDED_BUILDING_IDS)

        save_json_func(data)
        refresh_preview()
        buildings_button.config(state="disabled", text="All buildings unlocked")
        messagebox.showinfo(
            "Buildings",
            f"Added {b_added} new buildings (existing entries kept). "
            f"Total: {len(progress['BuildingsUnlocked'])} buildings unlocked."
        )

    buildings_button = ttk.Button(
        buildings_frame, text=f"Unlock all buildings ({len(EMBEDDED_BUILDING_IDS)})",
        command=unlock_buildings)
    buildings_button.pack(side="left", padx=8, pady=7)
    if buildings_fully_unlocked():
        buildings_button.config(state="disabled", text="All buildings unlocked")

    # --- Unlock Picked-Up Items Section ---
    # Progress.ItemsPickedUp is the item compendium: a strict-mode-validated list
    # of item data-asset PersistenceIDs. Some crafting/building-menu entries are
    # gated behind having "seen" the relevant item, so filling this unlocks them.
    # EMBEDDED_ITEM_PICKUP_IDS is folder-filtered (no /Deleted/, [PH], (Expired))
    # to stay within strict-mode validation. Union only - never delete.
    pickup_frame = ttk.LabelFrame(tab, text="Unlock Picked-Up Items")
    pickup_frame.pack(fill="x", padx=10, pady=(10, 0))

    def unlock_pickups():
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Load a save first.")
            return
        added, total = unlock_ops.unlock_section(
            data, "ItemsPickedUp", EMBEDDED_ITEM_PICKUP_IDS)
        save_json_func(data)
        refresh_preview()
        pickup_button.config(state="disabled", text="All item types unlocked")
        messagebox.showinfo(
            "Picked-Up Items",
            f"Added {added} new item types (existing entries kept). "
            f"Total: {total} items marked as seen."
        )

    pickup_button = ttk.Button(
        pickup_frame,
        text=f"Unlock all item types ({len(EMBEDDED_ITEM_PICKUP_IDS)})",
        command=unlock_pickups)
    pickup_button.pack(side="left", padx=8, pady=7)
    if unlock_ops.is_fully_unlocked(data, "ItemsPickedUp", EMBEDDED_ITEM_PICKUP_IDS):
        pickup_button.config(state="disabled", text="All item types unlocked")

    # --- Unlock Sanguine Urns Section ---
    # Sanguine Urns expand the lifepool. They are tracked in
    # Progress.ShrinesUnlocked (32-char hex GUIDs). Max HP is DERIVED on load
    # (100 + 10 * count) - there is no stored max field - so adding urns expands
    # the pool automatically. We deliberately do NOT write Character.Health; the
    # player heals in-game after joining. Union only - never delete.
    urn_frame = ttk.LabelFrame(tab, text="Unlock Sanguine Urns")
    urn_frame.pack(fill="x", padx=10, pady=(10, 0))

    def unlock_urns():
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Load a save first.")
            return
        added, total = unlock_ops.unlock_section(
            data, "ShrinesUnlocked", EMBEDDED_SHRINE_IDS)
        max_hp = unlock_ops.computed_max_hp(data)
        save_json_func(data)
        refresh_preview()
        urn_button.config(state="disabled", text="All Sanguine Urns unlocked")
        messagebox.showinfo(
            "Sanguine Urns",
            f"Added {added} new urns (existing entries kept). "
            f"Total: {total} urns unlocked.\n"
            f"Max HP is now {max_hp} on next load (heal in-game to fill it)."
        )

    urn_button = ttk.Button(
        urn_frame,
        text=f"Unlock all Sanguine Urns ({len(EMBEDDED_SHRINE_IDS)})",
        command=unlock_urns)
    urn_button.pack(side="left", padx=8, pady=7)
    if unlock_ops.is_fully_unlocked(data, "ShrinesUnlocked", EMBEDDED_SHRINE_IDS):
        urn_button.config(state="disabled", text="All Sanguine Urns unlocked")

    # --- Unlock Mount Section ---
    mount_frame = ttk.LabelFrame(tab, text="Unlock Mount")
    mount_frame.pack(fill="x", padx=10, pady=(10, 0))

    # The save's MountsUnlockedList (and MountEquipped) accept ONLY
    # "MountDataAsset:<assetname>" ref strings. Anything else (e.g. a
    # TAG.Mounts.Type.* gameplay tag) corrupts the save and the game then fails
    # to load player state. Hard-filter to valid refs so a bad embedded list can
    # never reach a save file.
    ALL_MOUNT_TAGS = [t for t in EMBEDDED_MOUNT_TAGS
                      if isinstance(t, str) and t.startswith("MountDataAsset:")]
    # sensible default to equip if the slot is empty: prefer a Terrorbird ref
    DEFAULT_MOUNT = next((t for t in ALL_MOUNT_TAGS if "Terrorbird" in t),
                         (ALL_MOUNT_TAGS[0] if ALL_MOUNT_TAGS else None))

    def owned_mount_tags():
        # data can be None at startup (no save loaded yet); this runs at setup
        # time for the gray-out check, so guard it.
        if not isinstance(data, dict):
            return set()
        character = data.get("Character")
        if not isinstance(character, dict):
            return set()
        mount = character.get("Mount")
        if not isinstance(mount, dict):
            return set()
        unlocked = mount.get("MountsUnlockedList")
        return set(unlocked) if isinstance(unlocked, list) else set()

    def all_mounts_unlocked():
        return bool(ALL_MOUNT_TAGS) and set(ALL_MOUNT_TAGS).issubset(owned_mount_tags())

    def unlock_mount():
        if not isinstance(data, dict):
            messagebox.showerror("Error", "Load a save first.")
            return
        character = data.get("Character")
        if not isinstance(character, dict):
            messagebox.showerror("Error", "Character data not found.")
            return

        mount = character.get("Mount")
        if not isinstance(mount, dict):
            mount = {}
            character["Mount"] = mount

        # Merge (union) every known mount tag into the unlocked list; never wipe
        # tags the player already owns. The full tag list comes from the ue4ss
        # dump (build_mount_ids.py), so it always matches the current game.
        unlocked = mount.get("MountsUnlockedList")
        if not isinstance(unlocked, list):
            unlocked = []
        seen = set(unlocked)
        added = 0
        for tag in ALL_MOUNT_TAGS:
            if tag not in seen:
                unlocked.append(tag)
                seen.add(tag)
                added += 1
        mount["MountsUnlockedList"] = unlocked
        if not mount.get("MountEquipped") and DEFAULT_MOUNT:
            mount["MountEquipped"] = DEFAULT_MOUNT

        save_json_func(data)
        refresh_preview()
        mount_button.config(state="disabled", text="All mounts unlocked")
        messagebox.showinfo(
            "Mount Unlock",
            f"Unlocked {added} new mount(s). "
            f"Total: {len(unlocked)} of {len(ALL_MOUNT_TAGS)} known mounts."
        )

    # count actual mount variants (MountDataAsset refs) for the label, not the
    # extra per-type tags; fall back to total if only type tags are present.
    mount_count = (sum(1 for t in ALL_MOUNT_TAGS if t.startswith("MountDataAsset:"))
                   or len(ALL_MOUNT_TAGS))
    mount_button = ttk.Button(
        mount_frame, text=f"Unlock all mounts ({mount_count})",
        command=unlock_mount)
    mount_button.pack(side="left", padx=8, pady=7)
    if all_mounts_unlocked():
        mount_button.config(state="disabled", text="All mounts unlocked")

    # --- Reset Player Status Section ---
    status_frame = ttk.LabelFrame(tab, text="Reset Player Status")
    status_frame.pack(fill="x", padx=10, pady=(10, 0))

    def reset_player_status():
        character = data.get("Character")
        if not isinstance(character, dict):
            messagebox.showerror("Error", "Character not found.")
            return

        loadout = data.get("Loadout", {})
        if "1" in loadout and isinstance(loadout["1"], dict):
            loadout["1"]["VitalShield"] = 75

        character["Sustenance"] = {"SustenanceValue": 100, "SustenanceDecayBuffer": 0}
        character["Hydration"] = {"HydrationValue": 100, "HydrationDecayBuffer": 0}
        character["Toxicity"] = {"ToxicityValue": 0, "HighestToxicityValue": 0}
        character["Endurance"] = {"EnduranceValue": 100, "EnduranceDecayBuffer": 0}
        character["Health"] = {"CurrentValue": 100}
        character["Stamina"] = {"CurrentValue": 100}

        save_json_func(data)
        refresh_preview()
        messagebox.showinfo("Reset Player Status", "Player fully restored.")

    ttk.Button(status_frame, text="Apply", command=reset_player_status).pack(side="left", padx=8, pady=7)
