import json
import os
import unittest

import info_summary as isum

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "mini_full_save.json")


def load_full():
    with open(FIXTURE, "r", encoding="utf-8") as f:
        return json.load(f)


class BuildSummaryTests(unittest.TestCase):
    def test_full_save(self):
        s = isum.build_summary(load_full())
        self.assertEqual(s["name"], "Testarossa")
        self.assertEqual(s["mode"], "Creative")   # meta_data.char_type == 3
        self.assertEqual(s["total_level"], 100)   # 99 (maxed) + 1 (level 1)
        self.assertEqual(s["maxed_skills"], 1)
        self.assertEqual(s["skill_count"], 11)

    def test_mode_from_char_type(self):
        self.assertEqual(
            isum.build_summary({"meta_data": {"char_type": 0}})["mode"], "Normal")
        self.assertEqual(
            isum.build_summary({"meta_data": {"char_type": 4}})["mode"], "Custom")

    def test_missing_meta_defaults_normal(self):
        # A loaded save with no meta_data mirrors the General tab: Normal.
        s = isum.build_summary({"GameProgress": {}})
        self.assertEqual(s["mode"], "Normal")
        self.assertEqual(s["name"], isum.DASH)
        self.assertEqual(s["total_level"], 0)

    def test_non_dict_input(self):
        s = isum.build_summary(None)
        self.assertEqual(s["name"], isum.DASH)
        self.assertEqual(s["mode"], isum.DASH)
        self.assertEqual(s["skill_count"], 11)


if __name__ == "__main__":
    unittest.main()
