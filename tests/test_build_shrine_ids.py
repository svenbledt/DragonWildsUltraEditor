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
        self.b = _load("build_shrine_ids", "ue4ss_dumper/build_shrine_ids.py")

    def test_known_ids_are_hex_guids(self):
        self.assertEqual(len(self.b.KNOWN_SHRINE_IDS), 7)
        for g in self.b.KNOWN_SHRINE_IDS:
            self.assertTrue(self.b.is_hex_guid(g), g)

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
