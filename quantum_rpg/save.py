"""JSON save / load. Default folder: ./saves next to the game, else ~/.quantum_rpg/saves."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import GameState


def save_dir(game_path: Path) -> Path:
    local = Path(game_path) / "saves"
    try:
        local.mkdir(parents=True, exist_ok=True)
        probe = local / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return local
    except OSError:
        home = Path.home() / ".quantum_rpg" / "saves"
        home.mkdir(parents=True, exist_ok=True)
        return home


def slot_path(game_path: Path, slot: str) -> Path:
    safe = "".join(c for c in slot if c.isalnum() or c in ("-", "_")) or "slot1"
    return save_dir(game_path) / f"{safe}.json"


def write_save(game_path: Path, slot: str, state: "GameState") -> Path:
    path = slot_path(game_path, slot)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_save(game_path: Path, slot: str) -> dict:
    path = slot_path(game_path, slot)
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))
