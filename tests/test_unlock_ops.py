import unittest
import unlock_ops as uo


class MergeIdsTests(unittest.TestCase):
    def test_adds_only_new_preserving_order(self):
        cur = ["a", "b"]
        added = uo.merge_ids(cur, ["b", "c", "c", "d"])
        self.assertEqual(added, 2)
        self.assertEqual(cur, ["a", "b", "c", "d"])

    def test_no_new_returns_zero(self):
        cur = ["a", "b"]
        self.assertEqual(uo.merge_ids(cur, ["a", "b"]), 0)
        self.assertEqual(cur, ["a", "b"])


class UnlockSectionTests(unittest.TestCase):
    def test_creates_section_and_unions(self):
        data = {"Progress": {"ItemsPickedUp": ["x"]}}
        added, total = uo.unlock_section(data, "ItemsPickedUp", ["x", "y", "z"])
        self.assertEqual((added, total), (2, 3))
        self.assertEqual(data["Progress"]["ItemsPickedUp"], ["x", "y", "z"])

    def test_creates_missing_progress_and_section(self):
        data = {}
        added, total = uo.unlock_section(data, "ShrinesUnlocked", ["g1", "g2"])
        self.assertEqual((added, total), (2, 2))
        self.assertEqual(data["Progress"]["ShrinesUnlocked"], ["g1", "g2"])

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError):
            uo.unlock_section(None, "ItemsPickedUp", ["x"])


class FullyUnlockedTests(unittest.TestCase):
    def test_true_when_subset_present(self):
        data = {"Progress": {"R": ["a", "b", "c"]}}
        self.assertTrue(uo.is_fully_unlocked(data, "R", ["a", "b"]))

    def test_false_when_missing_one(self):
        data = {"Progress": {"R": ["a"]}}
        self.assertFalse(uo.is_fully_unlocked(data, "R", ["a", "b"]))

    def test_false_on_no_save(self):
        self.assertFalse(uo.is_fully_unlocked(None, "R", ["a"]))

    def test_empty_catalog_is_not_fully_unlocked(self):
        data = {"Progress": {"SomeSection": ["a", "b"]}}
        self.assertFalse(uo.is_fully_unlocked(data, "SomeSection", []))


class MaxHpTests(unittest.TestCase):
    def test_base_when_no_shrines(self):
        self.assertEqual(uo.computed_max_hp({"Progress": {}}), 100)

    def test_scales_ten_per_shrine(self):
        data = {"Progress": {"ShrinesUnlocked": ["g"] * 7}}
        self.assertEqual(uo.computed_max_hp(data), 170)
        data = {"Progress": {"ShrinesUnlocked": ["g"] * 3}}
        self.assertEqual(uo.computed_max_hp(data), 130)


if __name__ == "__main__":
    unittest.main()
