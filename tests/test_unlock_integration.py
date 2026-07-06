import copy
import os
import unittest

from core.save_file import SaveFile
from core import unlocks
import data.pickup_ids as pickup_ids

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "mini_save.json")


def load_sf():
    return SaveFile.load(FIXTURE)


class PickupUnlockTests(unittest.TestCase):
    def test_unions_full_catalog_and_keeps_existing(self):
        sf = load_sf()
        before_health = copy.deepcopy(sf.progress["Character"]["Health"])
        added, total = unlocks.unlock_all(sf, "pickups")
        picked = sf.progress["Progress"]["ItemsPickedUp"]
        # existing entry preserved
        self.assertIn("existingItemA", picked)
        # every catalog id now present
        self.assertTrue(set(pickup_ids.EMBEDDED_ITEM_PICKUP_IDS).issubset(set(picked)))
        # added == catalog size (fixture shares none of them)
        self.assertEqual(added, len(pickup_ids.EMBEDDED_ITEM_PICKUP_IDS))
        self.assertEqual(total, len(picked))
        # Health untouched
        self.assertEqual(sf.progress["Character"]["Health"], before_health)

    def test_fully_unlocked_detects_completion(self):
        sf = load_sf()
        unlocks.unlock_all(sf, "pickups")
        rows = {r["key"]: r for r in unlocks.categories(sf)}
        self.assertTrue(rows["pickups"]["done"])
        self.assertEqual(rows["pickups"]["have"], rows["pickups"]["total"])


class ShrineUnlockTests(unittest.TestCase):
    def test_unions_urns_without_touching_health(self):
        import data.shrine_ids as shrine_ids
        sf = load_sf()
        before_health = copy.deepcopy(sf.progress["Character"]["Health"])
        added, total = unlocks.unlock_all(sf, "urns")
        shrines = sf.progress["Progress"]["ShrinesUnlocked"]
        # pre-existing shrine preserved
        self.assertIn("EXISTINGSHRINE0000000000000000AA", shrines)
        # all catalog urns present
        self.assertTrue(set(shrine_ids.EMBEDDED_SHRINE_IDS).issubset(set(shrines)))
        self.assertEqual(added, len(shrine_ids.EMBEDDED_SHRINE_IDS))
        # Health object is byte-for-byte unchanged
        self.assertEqual(sf.progress["Character"]["Health"], before_health)

    def test_computed_max_hp_matches_count(self):
        import data.shrine_ids as shrine_ids
        sf = load_sf()
        unlocks.unlock_all(sf, "urns")
        n = len(sf.progress["Progress"]["ShrinesUnlocked"])
        self.assertEqual(unlocks.computed_max_hp(sf), 100 + 10 * n)


if __name__ == "__main__":
    unittest.main()
