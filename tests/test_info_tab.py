import json
import os
import unittest
import tkinter as tk
from tkinter import ttk

import tab_general

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "mini_full_save.json")


class FakeEditor:
    def __init__(self, data):
        self.data = data
        self.preview_text = None

    def refresh_json_preview(self):
        pass


def all_label_texts(widget):
    texts = []
    for child in widget.winfo_children():
        if isinstance(child, ttk.Label):
            texts.append(child.cget("text"))
        texts.extend(all_label_texts(child))
    return texts


class InfoTabTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        self.root.destroy()

    def test_summary_shows_character_details(self):
        with open(FIXTURE, "r", encoding="utf-8") as f:
            data = json.load(f)
        editor = FakeEditor(data)
        frame = ttk.Frame(self.root)
        tab_general.setup_general_tab(frame, editor)
        texts = all_label_texts(frame)
        self.assertIn("Testarossa", texts)
        self.assertIn("Creative", texts)
        self.assertIsNotNone(editor.preview_text)

    def test_empty_state_without_data(self):
        editor = FakeEditor(None)
        frame = ttk.Frame(self.root)
        tab_general.setup_general_tab(frame, editor)
        texts = all_label_texts(frame)
        self.assertTrue(any("Load a save" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
