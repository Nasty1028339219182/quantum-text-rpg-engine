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


def user_games_dir() -> Path:
    d = user_data_dir() / "games"
    d.mkdir(parents=True, exist_ok=True)
    return d


def author_games_dir() -> Path:
    if frozen():
        return user_games_dir()
    repo = games_dir()
    try:
        repo.mkdir(parents=True, exist_ok=True)
        probe = repo / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return repo
    except OSError:
        return user_games_dir()


def list_games(extra: Path | None = None) -> list[Path]:
    out: list[Path] = []
    seen = set()
    roots = [games_dir(), user_games_dir()]
    if extra is not None:
        roots.append(Path(extra))
    if not frozen():
        roots.append(author_games_dir())
    for root in roots:
        if root is None or not Path(root).exists():
            continue
        try:
            entries = sorted(Path(root).iterdir())
        except OSError:
            continue
        for p in entries:
            if p.is_dir() and (p / "game.yaml").exists() and p.resolve() not in seen:
                seen.add(p.resolve())
                out.append(p)
    return out
