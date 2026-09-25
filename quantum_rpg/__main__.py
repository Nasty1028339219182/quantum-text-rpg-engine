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
        from .tclfix import prepare

        prepare()
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Quantum RPG", text[-1800:])
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        from .cli import main

        if getattr(sys, "frozen", False) and len(sys.argv) <= 1:
            sys.argv.append("gui")
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        _crash_log()
        raise

