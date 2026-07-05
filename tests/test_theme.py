import unittest
import tkinter as tk
from tkinter import ttk

import theme


class StubStyle:
    def __init__(self, mapping):
        self._m = mapping

    def lookup(self, a, b):
        return self._m.get((a, b), "")


class PalettePureTests(unittest.TestCase):
    def test_current_mode_defaults_and_validates(self):
        self.assertEqual(theme.current_mode({}), theme.DARK)
        self.assertEqual(theme.current_mode({"theme": "light"}), theme.LIGHT)
        self.assertEqual(theme.current_mode({"theme": "bogus"}), theme.DARK)
        self.assertEqual(theme.current_mode(None), theme.DARK)

    def test_derive_palette_reads_live_values(self):
        s = StubStyle({("Treeview", "background"): "#111111",
                       ("TEntry", "foreground"): "#eeeeee"})
        pal = theme.derive_palette(s, theme.DARK)
        self.assertEqual(pal["bg"], "#111111")
        self.assertEqual(pal["fg"], "#eeeeee")
        self.assertEqual(pal["field_fg"], "#eeeeee")

    def test_derive_palette_falls_back_when_empty(self):
        pal = theme.derive_palette(StubStyle({}), theme.LIGHT)
        self.assertEqual(pal["bg"], "#fafafa")
        self.assertEqual(pal["fg"], "#1c1c1c")


class TkPaintTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        self.root.destroy()

    def test_should_paint_distinguishes_tk_from_ttk(self):
        self.assertTrue(theme.should_paint(tk.Frame(self.root)))
        self.assertTrue(theme.should_paint(tk.Label(self.root)))
        self.assertTrue(theme.should_paint(tk.LabelFrame(self.root)))
        self.assertFalse(theme.should_paint(ttk.Frame(self.root)))
        self.assertFalse(theme.should_paint(ttk.Label(self.root)))

    def test_apply_theme_returns_palette_and_paints_raw_widgets(self):
        pal = theme.apply_theme(self.root, theme.DARK)
        self.assertIn("bg", pal)
        frame = tk.Frame(self.root)
        text = tk.Text(frame)
        text.pack()
        frame.pack()
        theme.paint_tree(self.root, pal)
        self.assertEqual(str(frame.cget("background")), pal["bg"])
        self.assertEqual(str(text.cget("background")), pal["field_bg"])


if __name__ == "__main__":
    unittest.main()
