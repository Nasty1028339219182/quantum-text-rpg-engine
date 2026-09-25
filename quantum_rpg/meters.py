"""Author-defined meters. Hunger stays as it is. Thirst and the rest are YAML."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .util import loc

if TYPE_CHECKING:
    from .engine import Game


def specs(game: "Game") -> dict:
    raw = game.world.game.get("meters") or {}
    return raw if isinstance(raw, dict) else {}


def ensure(game: "Game") -> None:
    for mid, spec in specs(game).items():
        if not isinstance(spec, dict):
            continue
        game.state.meters.setdefault(str(mid), int(spec.get("start") or 0))


def tick(game: "Game") -> None:
    for mid, spec in specs(game).items():
        if not isinstance(spec, dict):
            continue
        step = int(spec.get("step") or 0)
        if not step:
            continue
        change(game, str(mid), step, silent=True)


def change(game: "Game", mid: str, delta: int, silent: bool = False) -> None:
    spec = specs(game).get(mid) or {}
    if not isinstance(spec, dict):
        return
    mx = int(spec.get("max") or 10)
    cur = int(game.state.meters.get(mid, spec.get("start") or 0))
    cur = max(0, min(mx, cur + int(delta)))
    game.state.meters[mid] = cur
    if not silent:
        game.say(f"{name(game, mid)} {cur}/{mx}")
    _hurt(game, mid, spec)


def rest(game: "Game") -> None:
    for mid, spec in specs(game).items():
        if isinstance(spec, dict) and "rest" in spec:
            game.state.meters[str(mid)] = int(spec.get("rest") or 0)


def name(game: "Game", mid: str) -> str:
    spec = specs(game).get(mid) or {}
    if not isinstance(spec, dict):
        return str(mid)
    return loc(spec.get("name") or mid, game.lang)


def rows(game: "Game") -> list[dict]:
    out = []
    for mid, spec in specs(game).items():
        if not isinstance(spec, dict):
            continue
        mx = int(spec.get("max") or 10)
        cur = int(game.state.meters.get(str(mid), spec.get("start") or 0))
        out.append({"id": str(mid), "label": name(game, str(mid)), "value": cur, "max": mx})
    return out


def _hurt(game: "Game", mid: str, spec: dict) -> None:
    if game.state.ended:
        return
    cur = int(game.state.meters.get(mid, 0))
    mx = int(spec.get("max") or 10)
    hurt = str(spec.get("hurt") or ("full" if int(spec.get("step") or 0) >= 0 else "empty"))
    dmg = int(spec.get("damage") or 0)
    if not dmg:
        return
    if hurt == "full" and cur < mx:
        return
    if hurt == "empty" and cur > 0:
        return
    if hurt not in ("full", "empty"):
        return
    game.state.player.hp = max(0, game.state.player.hp - dmg)
    game.say(f"{name(game, mid)} {cur}/{mx}  -{dmg}")
    if game.state.player.hp <= 0:
        from .i18n import t

        game.say(t(game.lang, "starved"))
        game.finish("lose")
