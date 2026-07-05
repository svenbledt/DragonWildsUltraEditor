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
        self.assertEqual(s["mode"], "Hardcore")
        self.assertEqual(s["total_level"], 100)   # 99 (maxed) + 1 (level 1)
        self.assertEqual(s["maxed_skills"], 1)
        self.assertEqual(s["skill_count"], 11)

    def test_normal_mode_and_missing_name(self):
        s = isum.build_summary({"Hardcore": 0, "GameProgress": {}})
        self.assertEqual(s["mode"], "Normal")
        self.assertEqual(s["name"], isum.DASH)
        self.assertEqual(s["total_level"], 0)

    def test_missing_hardcore_is_dash(self):
        s = isum.build_summary({"GameProgress": {}})
        self.assertEqual(s["mode"], isum.DASH)

    def test_non_dict_input(self):
        s = isum.build_summary(None)
        self.assertEqual(s["name"], isum.DASH)
        self.assertEqual(s["skill_count"], 11)


if __name__ == "__main__":
    unittest.main()
