"""Theme management: applies sv-ttk (Sun Valley) with a dark/light toggle and
paints raw-tk widgets (which sv-ttk does not theme) to match the active palette.

sv-ttk only styles ttk widgets. Raw tk widgets (Frame, Label, Button, Text,
Entry, Listbox, Canvas, Scrollbar, Toplevel, Menu, LabelFrame) keep OS-default
colors unless we recolor them, so after building any UI we walk the tree and
paint them. If sv-ttk cannot be imported (e.g. a broken frozen build), we fall
back to the built-in 'clam' theme so the app still launches.
"""
from tkinter import ttk

DARK = "dark"
LIGHT = "light"

# Per-mode fallback palette. bg/fg are normally read live from the active theme
# (Treeview background / TEntry foreground); the rest are Sun-Valley-ish constants.
_FALLBACK = {
    DARK: {"bg": "#1c1c1c", "fg": "#fafafa", "field_bg": "#2b2b2b",
           "field_fg": "#fafafa", "select_bg": "#2f5b7c", "select_fg": "#ffffff",
           "border": "#3a3a3a"},
    LIGHT: {"bg": "#fafafa", "fg": "#1c1c1c", "field_bg": "#ffffff",
            "field_fg": "#1c1c1c", "select_bg": "#cfe6ff", "select_fg": "#1c1c1c",
            "border": "#d0d0d0"},
}

# Raw-tk widget class names that receive painting (never ttk widgets, whose class
# names start with 'T', e.g. 'TFrame'/'TLabel'/'Treeview').
PAINTED_TK_TYPES = frozenset({
    "Tk", "Toplevel", "Frame", "Labelframe", "Label", "Button",
    "Text", "Entry", "Listbox", "Canvas", "Scrollbar", "Menu",
})


def current_mode(settings):
    mode = settings.get("theme", DARK) if isinstance(settings, dict) else DARK
    return mode if mode in (DARK, LIGHT) else DARK


def should_paint(widget):
    """True iff widget is a raw-tk widget we paint. ttk widgets return False."""
    return widget.winfo_class() in PAINTED_TK_TYPES


def derive_palette(style, mode):
    """Palette for `mode`, reading bg/fg live from the active theme where
    available and falling back to the per-mode constants otherwise."""
    pal = dict(_FALLBACK.get(mode, _FALLBACK[DARK]))
    bg = style.lookup("Treeview", "background")
    fg = style.lookup("TEntry", "foreground")
    if bg:
        pal["bg"] = bg
    if fg:
        pal["fg"] = fg
        pal["field_fg"] = fg
    return pal


def apply_theme(root, mode):
    """Apply `mode` (dark/light) and return the derived palette. Falls back to
    the 'clam' theme if sv-ttk is unavailable."""
    mode = mode if mode in (DARK, LIGHT) else DARK
    style = ttk.Style(root)
    try:
        import sv_ttk
        sv_ttk.set_theme(mode)
    except Exception:
        fb = _FALLBACK[mode]
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background=fb["bg"], foreground=fb["fg"],
                        fieldbackground=fb["field_bg"])
    return derive_palette(style, mode)


def paint_widget(widget, palette):
    """Best-effort recolor of one raw-tk widget; ignores options it lacks."""
    cls = widget.winfo_class()

    def setopt(**kw):
        for k, v in kw.items():
            try:
                widget.configure(**{k: v})
            except Exception:
                pass

    if cls in ("Tk", "Toplevel", "Frame", "Labelframe"):
        setopt(background=palette["bg"])
    elif cls == "Label":
        setopt(background=palette["bg"], foreground=palette["fg"])
    elif cls == "Button":
        setopt(background=palette["bg"], foreground=palette["fg"],
               activebackground=palette["field_bg"], activeforeground=palette["fg"],
               highlightbackground=palette["bg"])
    elif cls in ("Text", "Entry", "Listbox"):
        setopt(background=palette["field_bg"], foreground=palette["field_fg"],
               insertbackground=palette["fg"], selectbackground=palette["select_bg"],
               selectforeground=palette["select_fg"])
    elif cls == "Canvas":
        setopt(background=palette["field_bg"], highlightbackground=palette["bg"])
    elif cls == "Scrollbar":
        setopt(background=palette["field_bg"], troughcolor=palette["bg"])
    elif cls == "Menu":
        setopt(background=palette["bg"], foreground=palette["fg"])


def paint_tree(widget, palette):
    """Recursively paint `widget` and all descendants that should_paint."""
    try:
        if should_paint(widget):
            paint_widget(widget, palette)
    except Exception:
        pass
    for child in widget.winfo_children():
        paint_tree(child, palette)
