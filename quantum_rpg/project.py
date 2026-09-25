"""Load / save a game folder for the editor. Unknown YAML keys are kept."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Optional

import yaml

from .paths import author_games_dir, frozen

FILES = (
    "game",
    "locations",
    "items",
    "npcs",
    "dialogues",
    "quests",
    "encounters",
    "recipes",
)


class Project:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.game: dict[str, Any] = {}
        self.locations: dict[str, dict] = {}
        self.items: dict[str, dict] = {}
        self.npcs: dict[str, dict] = {}
        self.dialogues: dict[str, dict] = {}
        self.quests: dict[str, dict] = {}
        self.encounters: dict[str, dict] = {}
        self.recipes: dict[str, dict] = {}
        self.abilities: dict[str, dict] = {}
        self.loot_tables: dict[str, dict] = {}
        self.events_text = ""
        self.hooks_text = ""
        self.dirty = False

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, path: str | Path) -> "Project":
        path = Path(path)
        p = cls(path)
        p.game = _load_map(path / "game.yaml")
        if not p.game:
            p.game = {"id": path.name, "title": path.name}
        p.locations = _load_entities(path / "locations.yaml")
        p.items = _load_entities(path / "items.yaml")
        p.npcs = _load_entities(path / "npcs.yaml")
        p.dialogues = _load_entities(path / "dialogues.yaml")
        p.quests = _load_entities(path / "quests.yaml")
        p.encounters = _load_entities(path / "encounters.yaml")
        p.recipes = _load_entities(path / "recipes.yaml")
        p.abilities = _load_entities(path / "abilities.yaml")
        p.loot_tables = _load_loot(path / "loot_tables.yaml")
        ev = path / "events.yaml"
        p.events_text = ev.read_text(encoding="utf-8") if ev.exists() else ""
        hk = path / "hooks.py"
        p.hooks_text = hk.read_text(encoding="utf-8") if hk.exists() else ""
        p.dirty = False
        return p

    def table(self, kind: str) -> dict[str, dict]:
        return getattr(self, kind)

    def save(self, dest: Optional[Path] = None) -> Path:
        dest = Path(dest) if dest else self.path
        dest.mkdir(parents=True, exist_ok=True)
        _dump_doc(dest / "game.yaml", _strip_game(self.game))
        _dump_doc(dest / "locations.yaml", _strip_table(self.locations))
        _dump_doc(dest / "items.yaml", _strip_table(self.items))
        _dump_doc(dest / "npcs.yaml", _strip_table(self.npcs))
        _dump_doc(dest / "dialogues.yaml", _strip_table(self.dialogues))
        _dump_doc(dest / "quests.yaml", _strip_table(self.quests))
        _dump_doc(dest / "encounters.yaml", _strip_table(self.encounters))
        _dump_doc(dest / "recipes.yaml", _strip_table(self.recipes))
        _dump_optional(dest / "abilities.yaml", self.abilities)
        _dump_optional(dest / "loot_tables.yaml", self.loot_tables)
        (dest / "events.yaml").write_text(self.events_text or "", encoding="utf-8")
        (dest / "hooks.py").write_text(self.hooks_text or "", encoding="utf-8")
        self.path = dest
        self.dirty = False
        return dest

    def freeze(self) -> str:
        import json

        blob = {
            "game": self.game,
            "locations": self.locations,
            "items": self.items,
            "npcs": self.npcs,
            "dialogues": self.dialogues,
            "quests": self.quests,
            "encounters": self.encounters,
            "recipes": self.recipes,
            "abilities": self.abilities,
            "loot_tables": self.loot_tables,
            "events": self.events_text,
            "hooks": self.hooks_text,
        }
        return json.dumps(blob, sort_keys=True, ensure_ascii=False, default=str)

    def add(self, kind: str, eid: str, data: Optional[dict] = None) -> dict:
        table = self.table(kind)
        eid = _slug(eid)
        if not eid or eid in table:
            raise ValueError(eid)
        row = dict(data or _blank(kind, eid))
        row["id"] = eid
        table[eid] = row
        self.dirty = True
        return row

    def delete(self, kind: str, eid: str) -> None:
        self.table(kind).pop(eid, None)
        self.dirty = True

    def rename(self, kind: str, old: str, new: str) -> str:
        new = _slug(new)
        table = self.table(kind)
        if not new or new in table:
            raise ValueError(new)
        row = table.pop(old)
        row["id"] = new
        table[new] = row
        self._retarget(kind, old, new)
        self.dirty = True
        return new

    def _retarget(self, kind: str, old: str, new: str) -> None:
        if kind == "locations":
            start = self.game.get("start")
            if start == old:
                self.game["start"] = new
            elif isinstance(start, dict) and start.get("location") == old:
                start["location"] = new
            for loc in self.locations.values():
                exits = loc.get("exits") or {}
                for d, dest in list(exits.items()):
                    if dest == old:
                        exits[d] = new
                    elif isinstance(dest, dict) and dest.get("to") == old:
                        dest["to"] = new
                if loc.get("search", {}).get("reveal_exit"):
                    pass
            for npc in self.npcs.values():
                if npc.get("location") == old:
                    npc["location"] = new
        if kind == "items":
            for loc in self.locations.values():
                loc["items"] = [new if x == old else x for x in (loc.get("items") or [])]
                loc["hidden_items"] = [new if x == old else x for x in (loc.get("hidden_items") or [])]
            inv = (self.game.get("player") or {}).get("inventory") or []
            if old in inv:
                self.game.setdefault("player", {})["inventory"] = [new if x == old else x for x in inv]
        if kind == "npcs":
            for loc in self.locations.values():
                loc["npcs"] = [new if x == old else x for x in (loc.get("npcs") or [])]
        if kind == "dialogues":
            for npc in self.npcs.values():
                if npc.get("dialogue") == old:
                    npc["dialogue"] = new
        if kind == "encounters":
            for npc in self.npcs.values():
                if npc.get("encounter") == old:
                    npc["encounter"] = new


def copy_for_edit(src: Path) -> Path:
    """If src is not writable (bundled / frozen), copy into the author games folder."""
    src = Path(src)
    if _writable(src):
        return src
    dest = author_games_dir() / src.name
    if dest.resolve() == src.resolve():
        return dest
    if dest.exists():
        return dest
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("saves", "__pycache__"))
    return dest


def new_game(name: str, template: Path) -> Path:
    slug = _slug(name)
    dest = author_games_dir() / slug
    if dest.exists():
        raise FileExistsError(str(dest))
    shutil.copytree(template, dest, ignore=shutil.ignore_patterns("saves", "__pycache__"))
    p = Project.load(dest)
    p.game["id"] = slug
    title = p.game.get("title")
    if isinstance(title, dict):
        title["ru"] = name
        title["en"] = name
    else:
        p.game["title"] = {"ru": name, "en": name}
    p.save()
    return dest


def loc_pair(val: Any) -> tuple[str, str]:
    if isinstance(val, dict):
        return str(val.get("ru") or ""), str(val.get("en") or "")
    s = "" if val is None else str(val)
    return s, s


def loc_value(ru: str, en: str) -> Any:
    ru, en = ru.strip(), en.strip()
    if not ru and not en:
        return None
    if ru and not en:
        return {"ru": ru}
    if en and not ru:
        return {"en": en}
    return {"ru": ru, "en": en}


def csv_load(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(str(x) for x in val if x is not None)
    return str(val)


def csv_dump(text: str) -> list[str]:
    return [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]


def yaml_load_text(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        return None
    return yaml.safe_load(text)


def yaml_dump_text(data: Any) -> str:
    if data in (None, "", [], {}):
        return ""
    return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()


def _slug(s: str) -> str:
    out = []
    for ch in (s or "").strip().replace(" ", "_"):
        if ch.isalnum() or ch in "_-":
            out.append(ch)
    return "".join(out)


def _writable(path: Path) -> bool:
    if frozen():
        # bundled resources live in a temp extract dir
        try:
            from .paths import bundle_root

            if bundle_root() in path.resolve().parents or path.resolve().is_relative_to(bundle_root()):
                return False
        except Exception:
            pass
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _load_map(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _load_loot(path: Path) -> dict[str, dict]:
    raw = _load_map(path)
    out: dict[str, dict] = {}
    for k, v in raw.items():
        if str(k).startswith("#") or v is None:
            continue
        if isinstance(v, list):
            out[str(k)] = {"id": k, "drops": v}
        elif isinstance(v, dict):
            row = dict(v)
            row.setdefault("id", k)
            if "drops" not in row and any(isinstance(x, dict) and "item" in x for x in (row.get("loot") or [])):
                row["drops"] = row.pop("loot")
            row.setdefault("drops", row.get("drops") or [])
            out[str(k)] = row
    return out


def _dump_optional(path: Path, table: dict[str, dict]) -> None:
    if not table:
        if path.exists():
            path.unlink()
        return
    _dump_doc(path, _strip_table(table))


def _load_entities(path: Path) -> dict[str, dict]:
    raw = _load_map(path)
    out: dict[str, dict] = {}
    for k, v in raw.items():
        if str(k).startswith("#") or v is None:
            continue
        if not isinstance(v, dict):
            continue
        row = dict(v)
        row.setdefault("id", k)
        out[str(k)] = row
    return out


def _strip(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).startswith("_"):
                continue
            if v in (None, ""):
                continue
            out[k] = _strip(v)
        return out
    if isinstance(obj, list):
        return [_strip(x) for x in obj]
    return obj


def _strip_game(game: dict) -> dict:
    return _strip(game)


def _strip_table(table: dict[str, dict]) -> dict:
    out = {}
    for eid, row in table.items():
        body = {k: v for k, v in _strip(row).items() if k != "id"}
        out[eid] = body
    return out


def _dump_doc(path: Path, data: Any) -> None:
    text = yaml.dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=88,
    )
    path.write_text(text, encoding="utf-8")


def _blank(kind: str, eid: str) -> dict:
    name = {"ru": eid, "en": eid}
    if kind == "locations":
        return {"name": name, "description": name, "exits": {}, "items": [], "npcs": []}
    if kind == "items":
        return {"name": name, "type": "misc", "aliases": [eid]}
    if kind == "npcs":
        return {"name": name, "description": name, "dialogue": eid}
    if kind == "dialogues":
        return {
            "start": "start",
            "nodes": {
                "start": {
                    "text": name,
                    "choices": [{"text": {"ru": "Уйти.", "en": "Leave."}, "end": True}],
                }
            },
        }
    if kind == "quests":
        return {"name": name, "description": name}
    if kind == "encounters":
        return {"name": name, "hp": 8, "attack": "1d4", "xp": 5}
    if kind == "recipes":
        return {"name": name, "ingredients": [], "result": eid}
    if kind == "abilities":
        return {"name": name, "class": "", "mp": 2, "damage": "1d6", "text": name}
    if kind == "loot_tables":
        return {"drops": [{"item": "", "chance": 100}]}
    return {"name": name}
