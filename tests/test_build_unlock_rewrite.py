import ast
import os
import shutil
import tempfile
import unittest
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REAL_UNLOCK_IDS = os.path.join(ROOT, "data", "unlock_ids.py")


def _load(mod_name, rel_path):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(ROOT, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _extract_block(text, key):
    """Return the exact source text of the `key = [...]` assignment (span-aware:
    from the line starting with "key =" through the first subsequent line whose
    stripped content ends with "]", inclusive)."""
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        if lines[i].startswith(key + " ="):
            start = i
            while i < len(lines) and not lines[i].strip().endswith("]"):
                i += 1
            return "".join(lines[start:i + 1])
        i += 1
    raise AssertionError(f"{key} assignment not found")


class BuildUnlockRewriteTests(unittest.TestCase):
    """Exercises the span-aware EMBEDDED_* rewrite() helper (shared shape across
    build_recipe_ids.py / build_building_ids.py / build_mount_ids.py) against a
    scratch copy of the real data/unlock_ids.py, so a regeneration run can never
    corrupt the other two embedded lists."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.tmp_unlock_ids = os.path.join(self.tmpdir, "unlock_ids.py")
        with open(REAL_UNLOCK_IDS, "r", encoding="utf-8") as f:
            self.original_text = f.read()
        shutil.copy(REAL_UNLOCK_IDS, self.tmp_unlock_ids)
        self.mod = _load("build_recipe_ids", "tools/ue4ss_dumper/build_recipe_ids.py")

    def test_rewrite_replaces_only_target_list(self):
        new_ids = ["NewRecipeId1", "NewRecipeId2"]
        self.mod.rewrite(new_ids, path=self.tmp_unlock_ids)

        with open(self.tmp_unlock_ids, "r", encoding="utf-8") as f:
            rewritten_text = f.read()

        # (a) still valid Python
        ast.parse(rewritten_text)

        # (b) the target list now holds exactly the new ids
        ns = {}
        exec(compile(rewritten_text, self.tmp_unlock_ids, "exec"), ns)  # noqa: S102
        self.assertEqual(ns["EMBEDDED_RECIPE_IDS"], new_ids)

        # (c) the other two EMBEDDED_* lists are byte-identical/unchanged
        for other_key in ("EMBEDDED_BUILDING_IDS", "EMBEDDED_MOUNT_TAGS"):
            self.assertEqual(
                _extract_block(self.original_text, other_key),
                _extract_block(rewritten_text, other_key),
                f"{other_key} block changed unexpectedly",
            )

        # a .bak backup of the pre-rewrite content was made next to the target
        bak_path = self.tmp_unlock_ids + ".bak"
        self.assertTrue(os.path.exists(bak_path))
        with open(bak_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), self.original_text)


if __name__ == "__main__":
    unittest.main()
