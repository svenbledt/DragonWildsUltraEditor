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


if __name__ == "__main__":
    unittest.main()
