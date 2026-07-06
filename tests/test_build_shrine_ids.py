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


class ShrineBuildTests(unittest.TestCase):
    def setUp(self):
        self.b = _load("build_shrine_ids", "tools/game_dump/build_shrine_ids.py")

    def test_known_ids_are_hex_guids(self):
        # The complete set is 18, extracted authoritatively from the cooked game
        # files (CUE4Parse + usmap, every BP_HealthShrine_C UniqueShrineIdentifier).
        # Assert the full count plus validity/uniqueness.
        self.assertEqual(len(self.b.KNOWN_SHRINE_IDS), 18)
        self.assertEqual(len(self.b.KNOWN_SHRINE_IDS),
                         len(set(self.b.KNOWN_SHRINE_IDS)))
        for g in self.b.KNOWN_SHRINE_IDS:
            self.assertTrue(self.b.is_hex_guid(g), g)

    def test_known_set_contains_all_previously_confirmed(self):
        # The 8 GUIDs confirmed earlier (save-harvested + the in-game-verified
        # 186B...) must all survive in the complete authoritative set.
        confirmed = {
            "824A3798412A1067890E86A2AEB609FF",
            "DB621D2A40316F7B97255696742C2AA1",
            "7DE4A84C4997053BD7171089B408AE13",
            "485514AA4D440FC3EBF331B6F5128ECE",
            "DCF55CC14E4019584B5B03AB1D1ECC75",
            "13A95FDF40A30E7465E66C96CAA63778",
            "BA041CF14868F751575411B22EFE218A",
            "186B64E241A3790BE54292A84653E981",
        }
        self.assertTrue(confirmed.issubset(set(self.b.KNOWN_SHRINE_IDS)))

    def test_is_hex_guid_rejects_base64_pid(self):
        self.assertFalse(self.b.is_hex_guid("fS-ZKE_Ymkc-RL-2ySIl9A"))
        self.assertFalse(self.b.is_hex_guid("824A3798412A1067890E86A2AEB609F"))  # 31 chars

    def test_build_ids_unions_known_and_keeps_only_hex(self):
        records = [
            {"PersistenceID": "13A95FDF40A30E7465E66C96CAA63778"},  # already known
            {"PersistenceID": "AABBCCDD11223344556677889900AABB"},  # new hex
            {"PersistenceID": "fS-ZKE_Ymkc-RL-2ySIl9A"},            # base64 -> rejected
        ]
        ids = self.b.build_ids(records)
        self.assertIn("AABBCCDD11223344556677889900AABB", ids)
        self.assertNotIn("fS-ZKE_Ymkc-RL-2ySIl9A", ids)
        # all known ids present (union)
        self.assertTrue(set(self.b.KNOWN_SHRINE_IDS).issubset(set(ids)))

    def test_validate_reports_missing_known(self):
        self.assertEqual(self.b.validate(self.b.KNOWN_SHRINE_IDS), [])
        partial = self.b.KNOWN_SHRINE_IDS[:-1]
        self.assertEqual(self.b.validate(partial), [self.b.KNOWN_SHRINE_IDS[-1]])


if __name__ == "__main__":
    unittest.main()
