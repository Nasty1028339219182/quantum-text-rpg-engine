"""Tcl cannot start if the unpacked exe sits in a path that is not Latin."""

from __future__ import annotations

import os
import shutil
import sys


def prepare() -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    home = getattr(sys, "_MEIPASS", "")
    if not home or _latin(home):
        return
    src_tcl = os.path.join(home, "_tcl_data")
    src_tk = os.path.join(home, "_tk_data")
    if not os.path.isdir(src_tcl):
        return
    root = os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "Temp", "QuantumRPG")
    try:
        os.makedirs(root, exist_ok=True)
    except OSError:
        root = os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"), "QuantumRPG")
        os.makedirs(root, exist_ok=True)
    _copy(src_tcl, os.path.join(root, "_tcl_data"))
    _copy(src_tk, os.path.join(root, "_tk_data"))
    os.environ["TCL_LIBRARY"] = os.path.join(root, "_tcl_data")
    os.environ["TK_LIBRARY"] = os.path.join(root, "_tk_data")


def _latin(path: str) -> bool:
    try:
        path.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def _copy(src: str, dest: str) -> None:
    if not os.path.isdir(src) or os.path.isdir(dest):
        return
    shutil.copytree(src, dest)
