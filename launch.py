"""Windows exe entry. Absolute imports only: PyInstaller runs this as a script."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


def _crash_log() -> None:
    text = traceback.format_exc()
    places = [Path.home() / "QuantumRPG-error.log"]
    if getattr(sys, "frozen", False):
        places.insert(0, Path(sys.executable).with_name("QuantumRPG-error.log"))
    for path in places:
        try:
            path.write_text(text, encoding="utf-8")
        except OSError:
            pass
    try:
        from quantum_rpg.tclfix import prepare

        prepare()
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Quantum RPG", text[-1800:])
        root.destroy()
    except Exception:
        pass


def start() -> int:
    from quantum_rpg.tclfix import prepare

    prepare()
    from quantum_rpg.cli import main

    if getattr(sys, "frozen", False) and len(sys.argv) <= 1:
        sys.argv.append("gui")
    return main()


if __name__ == "__main__":
    try:
        raise SystemExit(start())
    except SystemExit:
        raise
    except Exception:
        _crash_log()
        raise
