"""
loadout_presets.py - region x class best-in-slot templates for BOTH the gear
(inventory/loadout) tab and the storage tab.

Everything is defined ONCE here, by English item NAME, so the two tabs stay in
sync and picks are easy to tweak.

Regions come from the confirmed progression on the continent of Ashenfall
(Brynmoor -> Ghornfell -> Fellhollow -> Dowdun Reach -> Umbral Sands). Region ==
Power Level: Brynmoor PL2-3, Ghornfell PL3-4, Fellhollow PL5, Dowdun Reach PL6,
Umbral Sands PL7 (endgame). For each region x combat style (Melee / Ranged /
Magic) we pick the strongest kit at that Power Level.

Item picks are verified against the official wiki as of game version 0.12.0.8
(July 2026) AND confirmed present in this save's item_ids.py:
  - Melee  armour: Bronze->Iron->Steel->Black Knight(PL6)->Adamant(PL7)
  - Ranged armour: Leather->Studded->Green D'hide->Blue D'hide(PL6)->Red Dragon(PL7)
  - Magic  armour: Wizard->Dragonkin->Splitbark->Mystic(PL6)->Infinity Robes(PL7)
  - Endgame weapons: TokTz-Xil-Ak (melee), Bow of Elidinis (ranged), Master's Staff (magic)
  - Ammo:  Bronze->Iron->Steel->Mithril->Adamant Arrow
  - Combat runes: Water / Fire / Air (the three usable in combat)
  - Best healing food: cooked fish (highest HP restore after the June 2026 rework)

The equip-slot SKELETON (slot indices, VitalShield per slot, PlayerInventory
refs) is copied verbatim from the proven working loadouts - we only swap the
ItemData id per slot, so equip behaviour is unchanged.
"""
from collections import OrderedDict
from data.item_ids import ITEM_LIST

# ---------------------------------------------------------------------------
# name <-> id maps
# ---------------------------------------------------------------------------
_NAME_TO_ID = {}
_ID_TO_NAME = {}
_ID_TO_DUR = {}
for _it in ITEM_LIST:
    _n = _it.get("SourceString")
    _p = _it.get("PersistenceID")
    if _n and _p:
        _NAME_TO_ID.setdefault(_n, _p)
        _ID_TO_NAME.setdefault(_p, _n)
        _ID_TO_DUR[_p] = _it.get("Durability")

# Expired / deprecated items must NEVER enter a template (storage OR inventory).
# The game deprecates an item by spawning an "<name> (Expired)" twin; the base
# item keeps its old, functional-looking record in a pre-rework catalog dump but
# is non-functional in-game. So we treat as expired:
#   (a) anything whose name contains "(Expired)", and
#   (b) any base name that HAS an "(Expired)" twin (e.g. Weak/Lesser Healing
#       Potion - the twin is the game's fingerprint for a deprecated item).
# NB: PowerLevel == -1 is NOT used - it merely means "no combat power level" and
# legitimately covers 400+ items (capes, seeds, rings, tools), so it would wrongly
# exclude real gear. Every placement path consults _EXPIRED_PIDS;
# test_no_expired_in_presets guards against regressions.
_expired_bases = set()
for _it in ITEM_LIST:
    _n = _it.get("SourceString") or ""
    if _n.endswith("(Expired)"):
        _expired_bases.add(_n[: -len(" (Expired)")].strip())
_EXPIRED_PIDS = set()
for _it in ITEM_LIST:
    _n = _it.get("SourceString") or ""
    _p = _it.get("PersistenceID")
    if not _p:
        continue
    if "(Expired)" in _n or _n in _expired_bases:
        _EXPIRED_PIDS.add(_p)

# (c) Some items were deprecated in-game WITHOUT the catalog spawning an
# "(Expired)" twin, so the fingerprint above cannot see them. The Umbral Sands
# rework cut the ENTIRE healing-potion line this way: the base "Healing Potion"
# still carries a functional-looking record but is expired/non-functional
# in-game (healing now comes from food). List such twinless-deprecated items by
# name here so the guard blocks them everywhere.
_MANUALLY_EXPIRED_NAMES = {"Healing Potion"}
for _it in ITEM_LIST:
    if (_it.get("SourceString") or "") in _MANUALLY_EXPIRED_NAMES:
        _p = _it.get("PersistenceID")
        if _p:
            _EXPIRED_PIDS.add(_p)


def _is_expired(pid):
    """True if `pid` is an expired/deprecated item that must not be placed."""
    return pid in _EXPIRED_PIDS

# For a maxed item we want its FULL durability. The catalog's `Durability` field
# IS the item's max (verified: worn items in real saves sit below this value,
# never above). But many newer PL7 items (Obsidian, TokTz, tools, bows, staves)
# have no Durability in the catalog dump - for those we stamp a high sentinel so
# the game shows them full instead of -1 (this is exactly what real saves store
# for those items, e.g. 9999).
MAX_DUR_FALLBACK = 9999

# Backs/capes are NOT durability items (they never carry a Durability field in
# real saves) - never fabricate one for them.
_NO_DURABILITY_SUFFIXES = ("Cape",)


def _id(name):
    """Resolve an English item name to its PersistenceID (None if missing)."""
    return _NAME_TO_ID.get(name)


def _wants_durability(pid):
    """True unless this item is a no-durability type (a cape/back)."""
    nm = _ID_TO_NAME.get(pid, "")
    return not any(nm.endswith(sfx) for sfx in _NO_DURABILITY_SUFFIXES)


def _max_dur(pid):
    """Full/max durability to stamp on a non-stackable item, or None if the item
    should carry no durability field at all (capes)."""
    if not _wants_durability(pid):
        return None
    d = _ID_TO_DUR.get(pid)
    return d if isinstance(d, int) and d > 0 else MAX_DUR_FALLBACK


# Back-compat aliases: every placed non-stackable item now gets MAX durability.
def _dur(pid, fallback=MAX_DUR_FALLBACK):
    d = _max_dur(pid)
    return d if d is not None else fallback


def _real_dur(pid):
    """Max durability, or None for no-durability items (capes)."""
    return _max_dur(pid)


# ---------------------------------------------------------------------------
# Regions & classes (progression order)
# ---------------------------------------------------------------------------
REGIONS = ["Brynmoor", "Ghornfell", "Fellhollow", "Dowdun Reach", "Umbral Sands"]
CLASSES = ["Melee", "Ranged", "Magic"]

# Tier index 0..4 maps 1:1 onto REGIONS above.
# Every ladder below has exactly 5 entries (early -> endgame).

# Ladders below: index 0..4 -> Brynmoor / Ghornfell / Fellhollow / Dowdun Reach /
# Umbral Sands (== Power Level 2-3 / 3-4 / 5 / 6 / 7). Verified vs the 0.12.0.8
# wiki and present in item_ids.py.
_MELEE = {
    # Scimitar/sword line (fast); endgame = TokTz-Xil-Ak (PL7 obsidian sword, 1H).
    "weapon": ["Bronze Sword", "Iron Sword", "Steel Scimitar", "Mithril Scimitar", "TokTz-Xil-Ak"],
    # Endgame off-hand = Dragonfire Shield (BiS), not Adamant Shield.
    "offhand": ["Bronze Shield", "Iron Shield", "Steel Shield", "Mithril Shield", "Dragonfire Shield"],
    # Endgame armour = Obsidian set (Helmet/Chest/Legs), not the Adamant set.
    "head": ["Bronze Helmet", "Iron Helmet", "White Full Helm", "Black Knight Helmet", "Obsidian Helmet"],
    "body": ["Bronze Platebody", "Iron Platebody", "White Platebody", "Black Knight Platebody", "Obsidian Chest"],
    "legs": ["Bronze Platelegs", "Iron Platelegs", "White Platelegs", "Black Knight Platelegs", "Obsidian Legs"],
    "cape": ["Attack Cape"] * 5,
    "amulet": ["Amulet of Strength"] * 5,
}

_RANGED = {
    # Longbow line (Oak PL3 -> Blightwood PL4 -> Willow PL5 -> Maple PL6);
    # endgame = Bow of Elidinis (PL7 masterwork).
    "weapon": ["Oak Longbow", "Blightwood Longbow", "Willow Longbow", "Maple Longbow", "Bow of Elidinis"],
    "ammo": ["Bronze Arrow", "Iron Arrow", "Steel Arrow", "Mithril Arrows", "Adamant Arrow"],
    "head": ["Leather Cowl", "Studded Leather Cowl", "Green Dragonhide Coif", "Blue Dragonhide Coif", "Red Dragon Helmet"],
    "body": ["Leather Body", "Studded Leather Body", "Green Dragonhide Body", "Blue Dragonhide Body", "Red Dragon Chest"],
    "legs": ["Leather Chaps", "Studded Leather Chaps", "Green Dragonhide Chaps", "Blue Dragonhide Chaps", "Red Dragon Legs"],
    "cape": ["Ranged Cape"] * 5,
    "amulet": ["Inspiring Amulet of Ranged"] * 5,
}

_MAGIC = {
    "weapon": ["Oak Battlestaff", "Blightwood Battlestaff", "Staff of Light", "Splitbark Staff", "Master's Staff"],
    "head": ["Wizard Hat", "Dragonkin Mage Hood", "Splitbark Helm", "Mystic Hat", "Infinity Robe Hat"],
    "body": ["Wizard Robes", "Dragonkin Mage Robes", "Splitbark Body", "Mystic Robes", "Infinity Robe Body"],
    "legs": ["Wizard Robe Legs", "Dragonkin Mage Robe Legs", "Splitbark Legs", "Mystic Robe Legs", "Infinity Robe Legs"],
    "cape": ["Magic Cape"] * 5,
    "amulet": ["Amulet of Magic"] * 5,
    # Combat runes = Water / Fire / Air (the three usable in combat), plus Earth
    # for autocast flexibility. Air sits at inventory slot 34 to match the proven
    # magic loadout ref (slot 6 -> inv 34).
    "runes": ["Water Rune", "Fire Rune", "Air Rune", "Earth Rune"],
}

_LADDERS = {"Melee": _MELEE, "Ranged": _RANGED, "Magic": _MAGIC}

# Consumables scale with the region tier (index 0..4).
# Best-heal food = cooked fish (top HP after the June 2026 rework); the 2nd entry
# is a region-appropriate buff meal (shock/poison/bleed resist etc.).
_FOOD = [
    ["Grilled Trout", "Meat Stew"],
    ["Fried Salmon", "Fruit Pie"],
    ["Roasted Lobster", "Hearty Stew"],
    ["Monkfish Skewers", "Wild Pie"],
    ["Sun Baked Sole", "Smoked Infernal Eel"],
]
# NOTE: the ENTIRE healing-potion line is expired/non-functional after the
# Umbral Sands rework - "Weak"/"Lesser Healing Potion" carry an "(Expired)" twin
# (the game's fingerprint for a deprecated item) and the base "Healing Potion"
# was cut without one (see _MANUALLY_EXPIRED_NAMES above). There is no functional
# healing potion, so templates place NONE - healing is provided by food (cooked
# fish is the top heal post-rework). The _EXPIRED_PIDS guard blocks all three.
_ANTIPOISON =["Weak Antipoison Potion", "Lesser Antipoison Potion", "Antipoison Potion", "Antipoison Potion", "Super Antipoison Potion"]
# Class-specific combat boost potion (magic only has the Lesser Magic Potion).
_BOOST = {
    "Melee": ["Weak Focused Attack Potion", "Lesser Attack Potion", "Focused Attack Potion", "Focused Attack Potion", "Super Focused Attack Potion"],
    "Ranged": ["Weak Focused Attack Potion", "Lesser Attack Potion", "Focused Attack Potion", "Focused Attack Potion", "Super Focused Attack Potion"],
    "Magic": ["Lesser Magic Potion"] * 5,
}
# Endgame-only extras (added from the tier they first appear).
_EXTRA_INFUSION = {
    "Melee": "Ferocious Infusion",
    "Ranged": "Evasive Infusion",
    "Magic": "Arcane Infusion",
}

# 2H best-in-slot melee weapon, carried in the inventory ALONGSIDE the 1H+shield
# set (Greatsword line -> TzHaar-Ket-Om maul at PL7). Melee only.
_MELEE_2H = ["Bronze Greatsword", "Iron Greatsword", "Steel Greatsword", "Mithril Greatsword", "TzHaar-Ket-Om"]

# Utility tools carried in every gear inventory (best tier, fixed - not scaled).
# Inventory only; storage never gets tools.
_TOOLS = ["Adamant Spade", "Adamant Logging Axe", "Adamant Pickaxe", "Yew Rod", "Adamant Watering Can"]

# Accessory ring per class. This build has no combat-stat ring, so these are the
# best survival/utility picks (Recoil reflects damage for the melee front-line).
_RING = {"Melee": "Ring of Recoil", "Ranged": "Ring of Life", "Magic": "Ring of Life"}

STACK = 5000          # generous stack for consumables in storage
AMMO_STACK = 99       # per arrow slot in the gear inventory
RUNE_STACK = 999

# Inventory tab boundaries (verified from real saves: 8-slot action bar + 3x8
# per tab). Both tabs import these so the "preserve runes/ammo/quest on apply"
# logic uses the same ranges the templates write into.
ACTION_BAR = (0, 7)
MAIN_TAB = (8, 31)
RUNE_TAB = (32, 55)
AMMO_TAB = (56, 79)
QUEST_TAB = (80, 103)
RUNE_TAB_START, RUNE_TAB_END = RUNE_TAB
AMMO_TAB_START, AMMO_TAB_END = AMMO_TAB
QUEST_TAB_START, QUEST_TAB_END = QUEST_TAB


# ---------------------------------------------------------------------------
# gear (inventory + loadout) builder - reuses the proven per-class skeleton
# ---------------------------------------------------------------------------
def _gear_entry(pid, vital_shield=None, count=None):
    e = {"GUID": "", "ItemData": pid}
    if count is not None:
        e["Count"] = count
    else:
        e["Durability"] = _dur(pid)
    if vital_shield is not None:
        e["VitalShield"] = vital_shield
    return e


def build_gear(region, cls):
    """Return {"Inventory": {...}, "Loadout": {...}} for one region x class."""
    tier = REGIONS.index(region)
    L = _LADDERS[cls]

    def pid(slot):
        return _id(L[slot][tier])

    head, body, legs = pid("head"), pid("body"), pid("legs")
    weapon = pid("weapon")

    inv = OrderedDict()
    loadout = OrderedDict()

    # Armour goes in the loadout equip slots 0..2 (proven VitalShield pattern).
    # NOTE: no cape/back is equipped. The BiS backs are level-99 skill capes,
    # which are gated on the matching skill level - force-equipping one would
    # require the player to also edit their levels. The cape is still provided
    # as a bank item in the storage kit, to equip manually if they qualify.
    if head:
        loadout["0"] = _gear_entry(head, vital_shield=25)
    if body:
        loadout["1"] = _gear_entry(body, vital_shield=25)
    if legs:
        loadout["2"] = _gear_entry(legs, vital_shield=0)

    if cls == "Melee":
        offhand = _id(L["offhand"][tier])
        inv["0"] = _gear_entry(offhand or weapon, vital_shield=0)
        inv["1"] = _gear_entry(weapon, vital_shield=0)
        loadout["7"] = {"PlayerInventoryItemIndex": 1}   # main-hand -> inv slot 1
        loadout["8"] = {"PlayerInventoryItemIndex": 0}   # off-hand  -> inv slot 0

    elif cls == "Ranged":
        ammo = _id(L["ammo"][tier])
        inv["0"] = _gear_entry(weapon, vital_shield=0)   # bow in the action bar
        # Arrows live in the AMMO tab (slots 56-79), NOT the action bar - this
        # matches the real inventory layout, so the ammo ref and the "preserve
        # ammo" apply-logic line up. Equipped ammo = the first ammo slot (56).
        for s in range(AMMO_TAB_START, AMMO_TAB_START + 7):   # 7 arrow stacks
            inv[str(s)] = _gear_entry(ammo, count=AMMO_STACK)
            inv[str(s)]["VitalShield"] = 0
        loadout["5"] = {"PlayerInventoryItemIndex": AMMO_TAB_START}  # ammo -> slot 56
        loadout["7"] = {"PlayerInventoryItemIndex": 0}   # bow  -> inv slot 0
        loadout["8"] = {"PlayerInventoryItemIndex": 0}

    else:  # Magic
        inv["0"] = _gear_entry(weapon, vital_shield=0)
        # runes at inventory slots 32..38 (Air lands on 34 for the loadout ref)
        for i, rune_name in enumerate(L["runes"]):
            rid = _id(rune_name)
            if not rid:
                continue
            slot = str(32 + i)
            e = {"GUID": "", "ItemData": rid, "Count": RUNE_STACK}
            if rune_name in ("Air Rune", "Fire Rune"):
                e["VitalShield"] = 0
            inv[slot] = e
        loadout["6"] = {"PlayerInventoryItemIndex": 34}  # Air Rune
        loadout["7"] = {"PlayerInventoryItemIndex": 0}   # staff
        loadout["8"] = {"PlayerInventoryItemIndex": 0}

    # Accessory ring is EQUIPPED in the loadout ring slot (4). Rings aren't
    # level-gated like the skill capes, so this is safe to force-equip.
    ring = _id(_RING[cls])
    if ring:
        loadout["4"] = _carry_entry(ring)

    # --- carried extras in the main inventory (slots 8+): 2H melee BiS (melee
    # only), accessory amulet, and best-tier utility tools. These are carried,
    # NOT equipped, so they never touch the proven equip skeleton.
    carry = []
    if cls == "Melee":
        carry.append(_id(_MELEE_2H[tier]))       # 2H alternative to 1H+shield
    carry.append(_id(L["amulet"][tier]))          # class combat amulet
    carry.extend(_id(t) for t in _TOOLS)          # gathering tools
    cslot = 8
    for cid in carry:
        if not cid or _is_expired(cid):
            continue
        inv[str(cslot)] = _carry_entry(cid)
        cslot += 1

    _finalise(inv)
    _finalise(loadout)
    return {"Inventory": inv, "Loadout": loadout}


def _carry_entry(pid):
    """A non-equipped inventory item, stamped with FULL/max durability (None for capes)."""
    e = {"GUID": "", "ItemData": pid, "VitalShield": 0}
    rd = _real_dur(pid)
    if rd is not None:
        e["Durability"] = rd
    return e


# ---------------------------------------------------------------------------
# storage builder - full kit + consumables laid out in slots 0..19
# ---------------------------------------------------------------------------
def build_storage(region, cls):
    """Return {"PersonalInventory": {...}} for one region x class (bank kit)."""
    tier = REGIONS.index(region)
    L = _LADDERS[cls]
    st = OrderedDict()
    slot = [0]

    def put(pid, vital_shield=None, count=None):
        if not pid or _is_expired(pid):
            return
        key = str(slot[0])
        if slot[0] > 19:
            return
        e = {"GUID": "", "ItemData": pid}
        if count is not None:
            e["Count"] = count
        else:
            rd = _real_dur(pid)
            if rd is not None:
                e["Durability"] = rd
        if vital_shield is not None:
            e["VitalShield"] = vital_shield
        st[key] = e
        slot[0] += 1

    def put_name(name, **kw):
        put(_id(name), **kw)

    # equipped gear (armour + weapon + off-hand/ammo)
    put(_id(L["head"][tier]), vital_shield=25)
    put(_id(L["body"][tier]), vital_shield=25)
    put(_id(L["legs"][tier]), vital_shield=0)
    put(_id(L["cape"][tier]), vital_shield=0)
    put(_id(L["weapon"][tier]), vital_shield=0)
    if cls == "Melee":
        put(_id(L["offhand"][tier]), vital_shield=0)
    elif cls == "Ranged":
        put(_id(L["ammo"][tier]), count=STACK)
    else:  # Magic - stack every combat rune
        for rune_name in L["runes"]:
            put(_id(rune_name), count=RUNE_STACK)

    # class amulet
    put(_id(L["amulet"][tier]), vital_shield=0)

    # food (best available in the region)
    for food in _FOOD[tier]:
        put_name(food, count=STACK)

    # combat potions (no heal potion exists post-rework - food is the heal)
    put_name(_BOOST[cls][tier], count=STACK)
    put_name(_ANTIPOISON[tier], count=STACK)
    if tier >= 3:  # endgame infusion
        put_name(_EXTRA_INFUSION[cls], count=STACK)
    if tier >= 4:  # Umbral Sands = red dragons -> antifire
        put_name("Super Antifire Potion", count=STACK)

    # accessory ring last: only lands if slots remain (put() caps at slot 19).
    # No tools in storage - inventory carries those.
    put(_id(_RING[cls]), vital_shield=0)

    _finalise(st)
    return {"PersonalInventory": st}


def _finalise(d):
    """Sort numeric slots and set MaxSlotIndex, matching the tabs' helper."""
    numeric = [(int(k), k) for k in d.keys() if k.isdigit()]
    numeric.sort()
    items = [(k, d[k]) for _, k in numeric]
    max_slot = numeric[-1][0] if numeric else -1
    d.clear()
    for k, v in items:
        d[k] = v
    d["MaxSlotIndex"] = max_slot


# ---------------------------------------------------------------------------
# pre-built dicts keyed "Region - Class" for the two tabs
# ---------------------------------------------------------------------------
GEAR_LOADOUTS = {}
STORAGE_PRESETS = {}
for _r in REGIONS:
    for _c in CLASSES:
        _key = f"{_r} - {_c}"
        GEAR_LOADOUTS[_key] = build_gear(_r, _c)
        STORAGE_PRESETS[_key] = build_storage(_r, _c)


def preset_key(region, cls):
    return f"{region} - {cls}"


# ---------------------------------------------------------------------------
# validation helper (run this file directly)
# ---------------------------------------------------------------------------
def _validate():
    missing = set()
    ladders_all = []
    for cls, L in _LADDERS.items():
        for slot, names in L.items():
            for n in names:
                ladders_all.append((cls, slot, n))
    for group in _FOOD:
        for n in group:
            ladders_all.append(("food", "-", n))
    for n in _ANTIPOISON:
        ladders_all.append(("potion", "-", n))
    for cls, lst in _BOOST.items():
        for n in lst:
            ladders_all.append((cls, "boost", n))
    for n in list(_EXTRA_INFUSION.values()) + ["Super Antifire Potion"]:
        ladders_all.append(("extra", "-", n))
    for n in _MELEE_2H + _TOOLS + list(_RING.values()):
        ladders_all.append(("extra", "-", n))
    for cls, slot, n in ladders_all:
        if _id(n) is None:
            missing.add(n)
    if missing:
        print(f"MISSING {len(missing)} item name(s) not in item_ids.py:")
        for n in sorted(missing):
            print("   ", n)
    else:
        print("OK - every item name resolves to an id.")
    print(f"\nBuilt {len(GEAR_LOADOUTS)} gear loadouts and {len(STORAGE_PRESETS)} storage kits "
          f"({len(REGIONS)} regions x {len(CLASSES)} classes).")


if __name__ == "__main__":
    _validate()
