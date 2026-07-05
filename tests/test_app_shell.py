import unittest
import tkinter as tk


class AppShellTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        self.root.destroy()

    def test_constructs_without_file_or_blocking_popup(self):
        # If the old modal "Features & Credits" popup were still fired in
        # __init__, this construction would block and the test would hang;
        # completing at all proves the forced popup is gone.
        from main_gui import DragonWildsUltraEditor
        app = DragonWildsUltraEditor(self.root)
        self.assertEqual(app.file_label.cget("text"), "No file loaded")
        self.assertEqual(app.status_var.get(), "Ready")
        self.assertTrue(hasattr(app, "show_about_dialog"))
        import sv_ttk
        self.assertIn(sv_ttk.get_theme(), ("dark", "light"))


if __name__ == "__main__":
    unittest.main()
