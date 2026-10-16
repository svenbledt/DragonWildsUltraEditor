import os
import unittest
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load(mod_name, rel_path):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(ROOT, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class KeepRecordTests(unittest.TestCase):
    def setUp(self):
        self.b = _load("build_pickup_ids", "tools/game_dump/build_pickup_ids.py")

    def test_keeps_normal_item(self):
        rec = {"PersistenceID": "good1", "SourceString": "Healing Potion",
               "__fullname": "X /Game/Gameplay/Items/Consumables/ITEM_Heal.ITEM_Heal"}
        self.assertTrue(self.b.keep_record(rec))

    def test_drops_deleted_folder(self):
        rec = {"PersistenceID": "del1", "SourceString": "Lesser Healing Potion (Expired)",
               "__fullname": "X /Game/Gameplay/Items/Deleted/ITEM_X.ITEM_X"}
        self.assertFalse(self.b.keep_record(rec))

    def test_drops_placeholder_name(self):
        rec = {"PersistenceID": "ph1", "SourceString": "[PH] Page",
               "__fullname": "X /Game/Gameplay/Items/ITEM_PH.ITEM_PH"}
        self.assertFalse(self.b.keep_record(rec))

    def test_drops_expired_name(self):
        rec = {"PersistenceID": "exp1", "SourceString": "Weak Healing Potion (Expired)",
               "__fullname": "X /Game/Gameplay/Items/ITEM_Exp.ITEM_Exp"}
        self.assertFalse(self.b.keep_record(rec))

    def test_drops_missing_pid(self):
        rec = {"SourceString": "No Id", "__fullname": "X /Game/Gameplay/Items/ITEM_N.ITEM_N"}
        self.assertFalse(self.b.keep_record(rec))

    def test_build_ids_dedupes_and_filters(self):
        recs = [
            {"PersistenceID": "a", "SourceString": "A", "__fullname": "/Game/Items/A.A"},
            {"PersistenceID": "a", "SourceString": "A", "__fullname": "/Game/Items/A.A"},
            {"PersistenceID": "b", "SourceString": "B (Expired)", "__fullname": "/Game/Items/B.B"},
        ]
        self.assertEqual(self.b.build_ids(recs), ["a"])


class RealDumpTests(unittest.TestCase):
    """Guards against filter regressions using the checked-in dump."""
    def setUp(self):
        self.b = _load("build_pickup_ids", "tools/game_dump/build_pickup_ids.py")
        self.recs = self.b.load_records(os.path.join(ROOT, "tools", "game_dump", "ItemDumper_items.jsonl"))

    def test_expected_count(self):
        self.assertEqual(len(self.b.build_ids(self.recs)), 1501)

    def test_expired_lesser_healing_excluded(self):
        ids = set(self.b.build_ids(self.recs))
        for pid in ("lPzqZUcSYtHIhWmVyYKJ_Q", "zwfSHEp0CHGOFuOzNQA2OQ", "-9Zin0B1C7GQgVKwKSR0hQ"):
            self.assertNotIn(pid, ids)

    def test_fire_cape_alwayscook_vestige_excluded(self):
        # DA_Consumable_Vestige_Armour_Cape_Fire (in /AlwaysCook/) breaks the
        # strict load in ItemsPickedUp. The real Fire Cape (ITEM_Cape_Fire)
        # must stay.
        ids = set(self.b.build_ids(self.recs))
        self.assertNotIn("NndX3U-UM-JVFaKvgrz8Eg", ids)
        self.assertIn("36kwMUzRF5L6DG-k7YgkSw", ids)

    def test_keeps_other_alwayscook_items(self):
        # The game moved real vestiges into /AlwaysCook/ (Icthlarian Fetish is
        # a quest reward the game itself writes to ItemsPickedUp).
        ids = set(self.b.build_ids(self.recs))
        self.assertIn("a5rs9Ub7jmlX89io81drhw", ids)
        rec = {"PersistenceID": "ac1", "SourceString": "Some Vestige",
               "__fullname": "X /UmbralSands/Gameplay/Items/AlwaysCook/DA_V.DA_V"}
        self.assertTrue(self.b.keep_record(rec))


if __name__ == "__main__":
    unittest.main()
