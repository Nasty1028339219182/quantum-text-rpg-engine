"""Install / frozen / user-data paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "quantum-rpg"


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    if frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def games_dir() -> Path:
    env = os.environ.get("QUANTUM_RPG_GAMES")
    if env:
        return Path(env)
    return bundle_root() / "games"


def user_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        d = base / APP_NAME
    else:
        d = Path.home() / ".quantum_rpg"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_games(extra: Path | None = None) -> list[Path]:
    out: list[Path] = []
    seen = set()
    for root in (games_dir(), extra):
        if root is None or not Path(root).exists():
            continue
        for p in sorted(Path(root).iterdir()):
            if p.is_dir() and (p / "game.yaml").exists() and p.resolve() not in seen:
                seen.add(p.resolve())
                out.append(p)
    return out
