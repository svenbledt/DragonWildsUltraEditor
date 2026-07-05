import tkinter as tk
from tkinter import ttk

from info_summary import build_summary


def setup_general_tab(tab, editor):
    # Clear previous widgets to avoid duplicates on rebuild.
    for widget in tab.winfo_children():
        widget.destroy()

    data = getattr(editor, "data", None)
    summary = build_summary(data)

    card = ttk.LabelFrame(tab, text="Character")
    card.pack(fill="x", padx=10, pady=(10, 6))

    if data is None:
        ttk.Label(card, text="Load a save to see character details.").grid(
            row=0, column=0, sticky="w", padx=10, pady=8)
    else:
        rows = [
            ("Character", summary["name"]),
            ("Mode", summary["mode"]),
            ("Total Level", str(summary["total_level"])),
            ("Maxed skills", "{}/{}".format(summary["maxed_skills"], summary["skill_count"])),
        ]
        for i, (label, value) in enumerate(rows):
            ttk.Label(card, text=label + ":").grid(
                row=i, column=0, sticky="w", padx=(10, 8), pady=3)
            ttk.Label(card, text=value).grid(
                row=i, column=1, sticky="w", padx=(0, 10), pady=3)

    json_frame = ttk.LabelFrame(tab, text="Raw JSON")
    json_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    editor.preview_text = tk.Text(json_frame, wrap="none", height=18)
    editor.preview_text.pack(fill="both", expand=True, padx=6, pady=6)
    editor.preview_text.configure(state="disabled", font=("Consolas", 10))

    editor.refresh_json_preview()
