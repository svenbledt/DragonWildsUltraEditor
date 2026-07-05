import os
import sys
import tkinter as tk
from main_gui import DragonWildsUltraEditor

ICON_NAME = "Dragonwilds_Editor.ico"


def resource_path(name):
    """Resolve a bundled data file both in dev and inside the PyInstaller exe.

    Frozen onefile builds extract data to sys._MEIPASS; from source it sits
    next to this script.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("DragonWilds: Ultra Editor")
    root.geometry("900x600")
    # default= applies the icon to the root and any Toplevel dialogs opened
    # later. Never let a missing/invalid icon stop the app from launching.
    try:
        root.iconbitmap(default=resource_path(ICON_NAME))
    except Exception:
        pass
    app = DragonWildsUltraEditor(root)
    root.mainloop()