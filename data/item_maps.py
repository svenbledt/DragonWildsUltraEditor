"""
item_maps.py - shared item name<->id maps for the add-item UIs.

Both the gear (tab_editor) and storage (tab_storage) tabs turn the raw ITEM_LIST
catalog into lookup maps used to populate their "add item" dropdowns. Some item
names are NOT unique in the catalog - e.g. there are 4 different "Ascension Core"
records, one per Power Level (PL4/5/6/7), and dozens of others ("Letter" x11,
"Ascension Shard" x4, ...). A plain name->id map collapses each of these to a
single selectable entry, so the player can only ever add ONE of them.

build_item_maps() gives every duplicate-named record a distinct, human-readable
label (preferring its Power Level, falling back to an index) so all variants are
individually searchable and selectable. Unique names are left untouched.
"""
from collections import Counter


def build_item_maps(items):
    """Return (id_to_name, name_to_id, id_to_guids, id_to_extra).

    id_to_name / name_to_id use a DISPLAY LABEL that is unique per catalog record;
    for duplicate SourceStrings the label carries a "(PL#)" or "(#n)" suffix.
    id_to_guids / id_to_extra remain keyed by PersistenceID.
    """
    id_to_name = {}
    name_to_id = {}
    id_to_guids = {}
    id_to_extra = {}

    # How many catalog records share each SourceString.
    name_counts = Counter(
        it.get("SourceString") for it in items
        if it.get("SourceString") and it.get("PersistenceID")
    )
    dup_index = {}  # SourceString -> running counter across its duplicates

    for item in items:
        name = item.get("SourceString")
        persistence_id = item.get("PersistenceID")
        if not (name and persistence_id):
            continue
        guids = item.get("GUIDs", [])
        durability = item.get("Durability")
        vital_shield = item.get("VitalShield")

        # Build a unique display label for duplicate names. Only a positive
        # PowerLevel is meaningful (the catalog uses -1 / None for "no PL").
        if name_counts[name] > 1:
            dup_index[name] = dup_index.get(name, 0) + 1
            idx = dup_index[name]
            pl = item.get("PowerLevel")
            has_pl = isinstance(pl, int) and pl > 0
            label = f"{name} (PL{pl})" if has_pl else f"{name} (#{idx})"
            # Same-PL duplicates (or any residual collision) get an index too.
            if label in name_to_id:
                label = f"{name} (PL{pl} #{idx})" if has_pl else f"{name} (#{idx})"
        else:
            label = name

        # Final safety net: never let two different records share a label.
        if label in name_to_id and name_to_id[label] != persistence_id:
            label = f"{label} [{str(persistence_id)[:6]}]"

        id_to_name[persistence_id] = label
        name_to_id[label] = persistence_id
        id_to_guids[persistence_id] = guids if isinstance(guids, list) else ([guids] if guids else [])
        extra = {}
        if durability is not None:
            extra["Durability"] = durability
        if vital_shield is not None:
            extra["VitalShield"] = vital_shield
        id_to_extra[persistence_id] = extra

    return id_to_name, name_to_id, id_to_guids, id_to_extra
