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


def value(game: "Game", mid: str) -> int:
    if mid in game.state.meters or mid in specs(game):
        return int(game.state.meters.get(mid, 0))
    if mid == "hunger":
        return int(game.state.hunger)
    return 0


def tick(game: "Game", reason: str = "move") -> None:
    for mid, spec in specs(game).items():
        if not isinstance(spec, dict):
            continue
        delta = _delta(spec, reason)
        if not delta:
            continue
        change(game, str(mid), delta, silent=True)


def change(game: "Game", mid: str, delta: int, silent: bool = False) -> None:
    spec = specs(game).get(mid) or {}
    if not isinstance(spec, dict):
        return
    mx = int(spec.get("max") or 10)
    old = int(game.state.meters.get(mid, spec.get("start") or 0))
    cur = max(0, min(mx, old + int(delta)))
    game.state.meters[mid] = cur
    if not silent:
        game.say(f"{name(game, mid)} {bar(cur, mx)} {cur}/{mx}")
    _bands(game, mid, spec, old, cur)
    _release(game, mid, spec, cur)
    _hurt(game, mid, spec)


def rest(game: "Game") -> None:
    for mid, spec in specs(game).items():
        if not isinstance(spec, dict):
            continue
        if "rest" in spec:
            game.state.meters[str(mid)] = int(spec.get("rest") or 0)
        elif spec.get("regen"):
            change(game, str(mid), -int(spec.get("regen") or 0), silent=True)
        _release(game, str(mid), spec, int(game.state.meters.get(str(mid), 0)))


def name(game: "Game", mid: str) -> str:
    spec = specs(game).get(mid) or {}
    if not isinstance(spec, dict):
        return str(mid)
    return loc(spec.get("name") or mid, game.lang)


def bar(cur: int, mx: int, width: int = 10) -> str:
    if mx <= 0:
        return "░" * width
    filled = max(0, min(width, round(width * cur / mx)))
    return "█" * filled + "░" * (width - filled)


def rows(game: "Game") -> list[dict]:
    out = []
    cfg = game.hunger_cfg() if hasattr(game, "hunger_cfg") else {}
    if cfg:
        mx = int(cfg.get("max") or 1)
        cur = int(game.state.hunger)
        from .i18n import t

        out.append({
            "id": "hunger",
            "label": t(game.lang, "hunger"),
            "value": cur,
            "max": mx,
            "bar": bar(cur, mx),
            "warn": cur >= mx,
        })
    for mid, spec in specs(game).items():
        if not isinstance(spec, dict):
            continue
        mx = int(spec.get("max") or 10)
        cur = int(game.state.meters.get(str(mid), spec.get("start") or 0))
        hurt = str(spec.get("hurt") or "full")
        ratio = cur / mx if mx else 0
        warn = ratio >= 0.8 if hurt != "empty" else ratio <= 0.2
        out.append({
            "id": str(mid),
            "label": name(game, str(mid)),
            "value": cur,
            "max": mx,
            "bar": bar(cur, mx),
            "warn": warn,
        })
    return out


def _delta(spec: dict, reason: str) -> int:
    if reason in spec and spec.get(reason) is not None:
        return int(spec.get(reason) or 0)
    if reason == "fight":
        return 0
    return int(spec.get("step") or 0)


def _hurt(game: "Game", mid: str, spec: dict) -> None:
    if game.state.ended:
        return
    cur = int(game.state.meters.get(mid, 0))
    mx = int(spec.get("max") or 10)
    hurt = str(spec.get("hurt") or ("full" if int(spec.get("step") or spec.get("move") or 0) >= 0 else "empty"))
    dmg = int(spec.get("damage") or 0)
    if not dmg or hurt not in ("full", "empty"):
        return
    if hurt == "full" and cur < mx:
        return
    if hurt == "empty" and cur > 0:
        return
    game.state.player.hp = max(0, game.state.player.hp - dmg)
    game.say(f"{name(game, mid)} {bar(cur, mx)} {cur}/{mx}  -{dmg}")
    if game.state.player.hp <= 0:
        from .i18n import t

        game.say(t(game.lang, "starved"))
        game.finish("lose")


def _bands(game: "Game", mid: str, spec: dict, old: int, new: int) -> None:
    hurt = str(spec.get("hurt") or "full")
    for band in spec.get("bands") or []:
        if not isinstance(band, dict):
            continue
        at = int(band.get("at") or 0)
        crossed = (old < at <= new) if hurt != "empty" else (old > at >= new)
        if not crossed:
            continue
        key = f"{mid}:{at}"
        if band.get("once", True) and key in game.state.meter_marks:
            continue
        game.state.meter_marks.add(key)
        text = loc(band.get("text"), game.lang)
        if text:
            game.say(text)
        if band.get("effects"):
            from . import effects

            effects.apply(game, band.get("effects"))


def _release(game: "Game", mid: str, spec: dict, cur: int) -> None:
    hurt = str(spec.get("hurt") or "full")
    for band in spec.get("bands") or []:
        if not isinstance(band, dict):
            continue
        at = int(band.get("at") or 0)
        if (hurt != "empty" and cur < at) or (hurt == "empty" and cur > at):
            game.state.meter_marks.discard(f"{mid}:{at}")
