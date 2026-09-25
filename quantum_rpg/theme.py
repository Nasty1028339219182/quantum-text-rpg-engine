"""Shared window chrome. No graphics — colors and widgets only."""

from __future__ import annotations

from .tclfix import prepare

prepare()
import tkinter as tk

C = {
    "bg": "#121212",
    "panel": "#1b1b1b",
    "fg": "#e8e4d9",
    "dim": "#8e8a82",
    "accent": "#c4a35a",
    "btn": "#2a2a2a",
    "btn_hi": "#3a3a3a",
    "line": "#2e2e2e",
    "danger": "#b54a4a",
    "ok": "#6a9e6d",
    "entry": "#1a1a1a",
}


def font_ui(size=10, bold=False):
    return ("Segoe UI", size, "bold" if bold else "normal")


def font_log(size=10):
    return ("Consolas", size)


class Btn(tk.Button):
    def __init__(self, master, **kw):
        kw.setdefault("bg", C["btn"])
        kw.setdefault("fg", C["fg"])
        kw.setdefault("activebackground", C["btn_hi"])
        kw.setdefault("activeforeground", C["fg"])
        kw.setdefault("relief", "flat")
        kw.setdefault("bd", 0)
        kw.setdefault("padx", 8)
        kw.setdefault("pady", 4)
        kw.setdefault("cursor", "hand2")
        kw.setdefault("font", font_ui(9))
        kw.setdefault("anchor", "w")
        kw.setdefault("highlightthickness", 0)
        super().__init__(master, **kw)


class Entry(tk.Entry):
    def __init__(self, master, **kw):
        kw.setdefault("bg", C["entry"])
        kw.setdefault("fg", C["fg"])
        kw.setdefault("insertbackground", C["accent"])
        kw.setdefault("relief", "flat")
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", C["line"])
        kw.setdefault("highlightcolor", C["accent"])
        kw.setdefault("font", font_ui(10))
        super().__init__(master, **kw)


class Text(tk.Text):
    def __init__(self, master, **kw):
        kw.setdefault("bg", C["entry"])
        kw.setdefault("fg", C["fg"])
        kw.setdefault("insertbackground", C["accent"])
        kw.setdefault("relief", "flat")
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", C["line"])
        kw.setdefault("highlightcolor", C["accent"])
        kw.setdefault("font", font_log(10))
        kw.setdefault("wrap", "word")
        kw.setdefault("padx", 8)
        kw.setdefault("pady", 6)
        super().__init__(master, **kw)
