import unittest

import leveling


class LevelingTests(unittest.TestCase):
    def test_level_boundaries(self):
        self.assertEqual(leveling.get_level_for_xp(0), 1)
        self.assertEqual(leveling.get_level_for_xp(33), 2)
        self.assertEqual(leveling.get_level_for_xp(999999), 98)
        self.assertEqual(leveling.get_level_for_xp(1000000), 99)

    def test_bad_input_defaults_to_one(self):
        self.assertEqual(leveling.get_level_for_xp("abc"), 1)
        self.assertEqual(leveling.get_level_for_xp(-5), 1)

    def test_xp_for_level_roundtrip(self):
        self.assertEqual(leveling.get_xp_for_level(1), 0)
        self.assertEqual(leveling.get_xp_for_level(2), 33)
        self.assertEqual(leveling.get_xp_for_level(99), 1000000)


if __name__ == "__main__":
    unittest.main()
