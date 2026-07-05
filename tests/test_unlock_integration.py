import copy
import json
import os
import unittest

import unlock_ops as uo
import pickup_ids

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "mini_save.json")


def load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as f:
        return json.load(f)


class PickupUnlockTests(unittest.TestCase):
    def test_unions_full_catalog_and_keeps_existing(self):
        data = load_fixture()
        before_health = copy.deepcopy(data["Character"]["Health"])
        added, total = uo.unlock_section(data, "ItemsPickedUp",
                                         pickup_ids.EMBEDDED_ITEM_PICKUP_IDS)
        picked = data["Progress"]["ItemsPickedUp"]
        # existing entry preserved
        self.assertIn("existingItemA", picked)
        # every catalog id now present
        self.assertTrue(set(pickup_ids.EMBEDDED_ITEM_PICKUP_IDS).issubset(set(picked)))
        # added == catalog size (fixture shares none of them)
        self.assertEqual(added, len(pickup_ids.EMBEDDED_ITEM_PICKUP_IDS))
        self.assertEqual(total, len(picked))
        # Health untouched
        self.assertEqual(data["Character"]["Health"], before_health)

    def test_fully_unlocked_detects_completion(self):
        data = load_fixture()
        uo.unlock_section(data, "ItemsPickedUp", pickup_ids.EMBEDDED_ITEM_PICKUP_IDS)
        self.assertTrue(uo.is_fully_unlocked(data, "ItemsPickedUp",
                                             pickup_ids.EMBEDDED_ITEM_PICKUP_IDS))


class ShrineUnlockTests(unittest.TestCase):
    def test_unions_urns_without_touching_health(self):
        import shrine_ids
        data = load_fixture()
        before_health = copy.deepcopy(data["Character"]["Health"])
        added, total = uo.unlock_section(data, "ShrinesUnlocked",
                                         shrine_ids.EMBEDDED_SHRINE_IDS)
        shrines = data["Progress"]["ShrinesUnlocked"]
        # pre-existing shrine preserved
        self.assertIn("EXISTINGSHRINE0000000000000000AA", shrines)
        # all catalog urns present
        self.assertTrue(set(shrine_ids.EMBEDDED_SHRINE_IDS).issubset(set(shrines)))
        self.assertEqual(added, len(shrine_ids.EMBEDDED_SHRINE_IDS))
        # Health object is byte-for-byte unchanged
        self.assertEqual(data["Character"]["Health"], before_health)

    def test_computed_max_hp_matches_count(self):
        import shrine_ids
        data = load_fixture()
        uo.unlock_section(data, "ShrinesUnlocked", shrine_ids.EMBEDDED_SHRINE_IDS)
        n = len(data["Progress"]["ShrinesUnlocked"])
        self.assertEqual(uo.computed_max_hp(data), 100 + 10 * n)


if __name__ == "__main__":
    unittest.main()
