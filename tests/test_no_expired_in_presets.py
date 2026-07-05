"""Guard: no loadout/storage template may place an expired/deprecated item.

The game deprecates an item by spawning an "<name> (Expired)" twin (PowerLevel
-1); loadout_presets._EXPIRED_PIDS captures those plus any base name that has
such a twin (e.g. Weak/Lesser Healing Potion). These tests fail if any preset
ever references one - in the inventory OR the storage kit.
"""
import unittest

import loadout_presets as lp


def _placed_pids(section):
    """Every ItemData id placed in a preset section (skips loadout ref slots)."""
    out = []
    for entry in section.values():
        if isinstance(entry, dict) and "ItemData" in entry:
            out.append(entry["ItemData"])
    return out


class NoExpiredInPresets(unittest.TestCase):
    def test_guard_found_the_known_expired_heals(self):
        # Sanity: the catalog-derived guard is non-empty and flags the two
        # deprecated heals by their functional-looking base ids.
        self.assertTrue(lp._EXPIRED_PIDS, "expired-pid guard is empty")
        for name in ("Weak Healing Potion", "Lesser Healing Potion"):
            pid = lp._NAME_TO_ID.get(name)
            self.assertIsNotNone(pid, name + " missing from catalog")
            self.assertTrue(lp._is_expired(pid), name + " not flagged expired")

    def test_healing_potion_is_not_flagged(self):
        # The one functional heal must remain placeable.
        pid = lp._NAME_TO_ID.get("Healing Potion")
        self.assertIsNotNone(pid)
        self.assertFalse(lp._is_expired(pid))

    def test_no_expired_item_in_any_gear_loadout(self):
        for key, gear in lp.GEAR_LOADOUTS.items():
            for sect in ("Inventory", "Loadout"):
                for pid in _placed_pids(gear.get(sect, {})):
                    self.assertNotIn(
                        pid, lp._EXPIRED_PIDS,
                        "expired item placed in gear %s / %s" % (key, sect))

    def test_no_expired_item_in_any_storage_preset(self):
        for key, store in lp.STORAGE_PRESETS.items():
            for pid in _placed_pids(store.get("PersonalInventory", {})):
                self.assertNotIn(
                    pid, lp._EXPIRED_PIDS,
                    "expired item placed in storage %s" % key)


if __name__ == "__main__":
    unittest.main()
