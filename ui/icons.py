"""Lazy CTkImage cache over data/icons. Icons are optional: any failure
returns None and the caller renders a text tile instead."""
import json
import os
import sys

import customtkinter as ctk
from PIL import Image


def app_root():
    """Folder holding data/ and the exe/scripts — works for `py main.py`
    (repo root) and for the Nuitka standalone folder (exe dir)."""
    if "__compiled__" in globals() or getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_ICON_DIR = os.path.join(app_root(), "data", "icons")
_manifest = None
_cache = {}


def _load_manifest():
    global _manifest
    if _manifest is None:
        try:
            with open(os.path.join(_ICON_DIR, "manifest.json"),
                      "r", encoding="utf-8") as f:
                _manifest = json.load(f)
        except Exception:
            _manifest = {}
    return _manifest


def get_icon(pid, size=32):
    key = (pid, size)
    if key in _cache:
        return _cache[key]
    img = None
    filename = _load_manifest().get(pid)
    if filename:
        try:
            pil = Image.open(os.path.join(_ICON_DIR, filename))
            img = ctk.CTkImage(light_image=pil, dark_image=pil,
                               size=(size, size))
        except Exception:
            img = None
    _cache[key] = img
    return img
