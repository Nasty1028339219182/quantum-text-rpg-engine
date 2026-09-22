"""Bundled YAML bricks for the editor and `include:` in game.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .paths import bundle_root, library_dir
from .util import loc

KINDS = ("locations", "items", "npcs", "dialogues", "quests", "encounters", "recipes", "loot_tables")


@dataclass
class Brick:
    kind: str
    eid: str
    file: Path
    data: dict
    title: Any = ""

    def label(self, lang: str) -> str:
        name = loc(self.title or self.data.get("name") or self.eid, lang)
        return f"{self.kind}/{self.eid}  —  {name}"


def catalog(root: Optional[Path] = None) -> list[Brick]:
    root = Path(root) if root else library_dir()
    if not root.exists():
        return []
    out: list[Brick] = []
    for path in sorted(root.rglob("*.yaml")):
        if path.name.lower() in ("index.yaml", "readme.yaml"):
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for kind, table in _split(raw, path).items():
            for eid, data in table.items():
                if not isinstance(data, dict):
                    continue
                out.append(
                    Brick(
                        kind=kind,
                        eid=str(eid),
                        file=path,
                        data=data,
                        title=data.get("name") or eid,
                    )
                )
    return out


def load_include(rel: str, game_dir: Path) -> dict[str, dict[str, dict]]:
    """Return {kind: {id: data}} from a path relative to the game or library/."""
    path = _resolve(rel, game_dir)
    if path is None or not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _split(raw, path)


def _resolve(rel: str, game_dir: Path) -> Optional[Path]:
    rel = str(rel).lstrip("/\\")
    candidates = [
        Path(game_dir) / rel,
        library_dir() / rel,
        bundle_root() / rel,
        library_dir() / Path(rel).name,
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def _split(raw: Any, path: Path) -> dict[str, dict[str, dict]]:
    if not raw:
        return {}
    out: dict[str, dict[str, dict]] = {}
    if isinstance(raw, dict):
        keys = [k for k in raw if k in KINDS]
        if keys:
            for k in keys:
                out.setdefault(k, {}).update(_as_table(raw[k]))
            return out
        # whole file is one kind, inferred from parent folder
        parent = path.parent.name
        kind = parent if parent in KINDS else "items"
        out[kind] = _as_table(raw)
        return out
    return out


def _as_table(data: Any) -> dict[str, dict]:
    if not data:
        return {}
    if isinstance(data, dict):
        table = {}
        for k, v in data.items():
            if isinstance(v, dict):
                row = dict(v)
                row.setdefault("id", k)
                table[str(k)] = row
            elif isinstance(v, list) and k:
                # loot table as a list
                table[str(k)] = {"id": k, "drops": v}
        return table
    if isinstance(data, list):
        table = {}
        for v in data:
            if isinstance(v, dict) and v.get("id"):
                table[str(v["id"])] = v
        return table
    return {}
