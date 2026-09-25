"""Turn-based text combat. Numbered menu + verb shortcuts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .effects import apply as apply_effects
from .abilities import available as available_abilities
from .abilities import resolve_choice as resolve_ability
from .i18n import t
from .parser import parse
from .util import loc, modifier, roll

if TYPE_CHECKING:
    from .engine import Game


@dataclass
class Fighter:
    id: str
    name: str
    hp: int
    max_hp: int
    attack: str
    defense: int
    ac_bonus: int = 0
    phrases: dict = field(default_factory=dict)
    loot: list = field(default_factory=list)
    xp: int = 0
    status: list = field(default_factory=list)


def _build_enemies(game: "Game", enc: dict) -> list[Fighter]:
    lang = game.lang
    if enc.get("enemies"):
        out = []
        counts: dict[str, int] = {}
        for ref in enc["enemies"]:
            src = game.world.encounters.get(ref, {"id": ref})
            counts[ref] = counts.get(ref, 0) + 1
            n = counts[ref]
            name = loc(src.get("name") or ref, lang)
            if n > 1:
                name = f"{name} {n}"
            out.append(_fighter_from(src, name, ref if n == 1 else f"{ref}_{n}"))
        return out
    name = loc(enc.get("name") or enc.get("id"), lang)
    return [_fighter_from(enc, name, enc.get("id") or "enemy")]


def _fighter_from(src: dict, name: str, fid: str) -> Fighter:
    hp = int(src.get("hp") or 8)
    return Fighter(
        id=fid,
        name=name,
        hp=hp,
        max_hp=hp,
        attack=str(src.get("attack") or "1d4"),
        defense=int(src.get("defense") or 0),
        ac_bonus=int(src.get("ac") or 0),
        phrases=src.get("phrases") or {},
        loot=list(src.get("loot") or []),
        xp=int(src.get("xp") or 0),
    )


def player_weapon(game: "Game") -> dict:
    eid = game.state.player.equipment.get("weapon")
    if eid and eid in game.world.items:
        return game.world.items[eid]
    for iid in game.state.player.inventory:
        item = game.world.items.get(iid) or {}
        if item.get("type") == "weapon":
            return item
    return {"damage": "1d2", "name": {"ru": "кулаки", "en": "fists"}}


def player_ac(game: "Game") -> int:
    p = game.state.player
    ac = 10 + modifier(int(p.stats.get("dex", 10)))
    for slot in ("armor", "shield", "accessory"):
        iid = p.equipment.get(slot)
        if iid and iid in game.world.items:
            ac += int(game.world.items[iid].get("ac") or 0)
    for s in p.status:
        ac += int(getattr(s, "ac", 0) or 0)
    return ac


def player_attack_bonus(game: "Game") -> int:
    p = game.state.player
    bonus = modifier(int(p.stats.get("str", 10)))
    w = player_weapon(game)
    bonus += int(w.get("hit") or w.get("bonus") or 0)
    for s in p.status:
        bonus += int(getattr(s, "attack", 0) or 0)
    return bonus


def run(game: "Game", encounter_id: str) -> str:
    enc = game.world.encounters.get(encounter_id)
    if not enc:
        game.say(t(game.lang, "gone"))
        return "none"
    game.in_combat = True
    game.combat_id = encounter_id
    enemies = _build_enemies(game, enc)
    appear = loc((enc.get("phrases") or {}).get("appear") or enc.get("appear"), game.lang)
    if appear:
        game.say(appear)
    else:
        names = ", ".join(e.name for e in enemies)
        game.say(f"--- {t(game.lang, 'combat')}: {names} ---")

    game.hooks.call("on_combat_start", game, encounter_id)

    defending = False
    while True:
        if game.state.ended:
            game.in_combat = False
            game.set_choices([])
            return "lose" if game.state.ended == "lose" else "win"
        living = [e for e in enemies if e.hp > 0]
        if not living:
            _victory(game, enc, enemies)
            game.in_combat = False
            game.set_choices([])
            game.hooks.call("on_combat_end", game, encounter_id, True)
            apply_effects(game, enc.get("on_win"))
            return "win"

        _status(game, living)
        rows = available_abilities(game)
        game.say(t(game.lang, "combat_menu"))
        choices = [
            {"label": t(game.lang, "attack"), "command": "1"},
            {"label": t(game.lang, "use_item"), "command": "2"},
            {"label": t(game.lang, "defend"), "command": "3"},
            {"label": t(game.lang, "flee"), "command": "4"},
        ]
        for i, (aid, spec) in enumerate(rows, 5):
            name = loc(spec.get("name") or aid, game.lang)
            cost = int(spec.get("mp") or 0)
            label = f"{i}. {name}" + (f" ({cost} MP)" if cost else "")
            game.say(f"  {label}")
            choices.append({"label": label, "command": str(i)})
        game.set_choices(choices)
        choice = (game.ui.read(t(game.lang, "prompt")) or "").strip().lower()
        cmd = parse(choice)
        if cmd and cmd.verb in (
            "save", "load", "language", "help", "stats", "inventory",
            "quests", "journal", "map", "quit",
        ):
            if cmd.verb == "quit":
                game.in_combat = False
                game.running = False
                game.set_choices([])
                return "abort"
            game.handle(choice)
            continue
        ability_id = resolve_ability(game, choice)
        if ability_id:
            if not _cast(game, ability_id, living):
                continue
            defending = False
        else:
            action, extra = _parse_choice(choice)

            if action in ("quit", "выход"):
                game.in_combat = False
                game.running = False
                game.set_choices([])
                return "abort"
            if action == "flee" or action == "4":
                dc = int(enc.get("flee_dc") or 12)
                roll_v = roll("1d20", game.rng) + modifier(int(game.state.player.stats.get("dex", 10)))
                if roll_v >= dc:
                    game.say(t(game.lang, "fled"))
                    game.in_combat = False
                    game.set_choices([])
                    game.hooks.call("on_combat_end", game, encounter_id, False)
                    return "flee"
                game.say(t(game.lang, "cant_flee"))
            elif action in ("defend", "3"):
                defending = True
                game.say(t(game.lang, "defending"))
            elif action in ("use", "2", "item"):
                _use_in_combat(game, extra, living)
            elif action in ("say",):
                handled = game.hooks.call("on_command", game, "say", extra.split() if extra else [])
                if not handled:
                    game.say(t(game.lang, "nothing_happens"))
            else:
                target = _pick_target(game, living, extra)
                if target:
                    _player_hit(game, target)
                defending = False

        living = [e for e in enemies if e.hp > 0]
        if not living or game.state.ended or not game.running:
            continue

        _allies_act(game, living)
        living = [e for e in enemies if e.hp > 0]
        if not living or game.state.ended or not game.running:
            continue

        ac = player_ac(game) + (2 if defending else 0)
        covered = False
        for enemy in living:
            ally = _cover_ally(game)
            if ally and not covered:
                _enemy_hit_ally(game, enemy, ally[0], ally[1])
                covered = True
            else:
                _enemy_hit(game, enemy, ac)
            if game.state.player.hp <= 0:
                game.say(t(game.lang, "dead"))
                game.finish("lose")
                game.in_combat = False
                game.set_choices([])
                game.hooks.call("on_combat_end", game, encounter_id, False)
                apply_effects(game, enc.get("on_lose"))
                return "lose"
        defending = False
        game.tick_status(in_combat=True)


def _parse_choice(choice: str) -> tuple[str, str]:
    if not choice:
        return "attack", ""
    parts = choice.split(None, 1)
    head, rest = parts[0], (parts[1] if len(parts) > 1 else "")
    aliases = {
        "1": "attack",
        "attack": "attack",
        "атаковать": "attack",
        "ударить": "attack",
        "hit": "attack",
        "2": "use",
        "use": "use",
        "item": "use",
        "предмет": "use",
        "использовать": "use",
        "3": "defend",
        "defend": "defend",
        "защищаться": "defend",
        "защита": "defend",
        "4": "flee",
        "flee": "flee",
        "бежать": "flee",
        "run": "flee",
        "say": "say",
        "сказать": "say",
        "произнести": "say",
        "quit": "quit",
        "выход": "quit",
    }
    return aliases.get(head, "attack"), rest or head if head not in aliases else rest


def _cover_ally(game: "Game"):
    for fid, data in (game.state.followers or {}).items():
        if data.get("cover") is False:
            continue
        if int(data.get("hp") or 0) <= 0:
            continue
        return fid, data
    return None


def _enemy_hit_ally(game: "Game", enemy: Fighter, fid: str, data: dict) -> None:
    name = game.npc_name(fid)
    ac = 10 + int(data.get("ac") or 0)
    to_hit = roll("1d20", game.rng) + int(enemy.defense)
    if to_hit < ac:
        game.say(t(game.lang, "ally_evade", name=name, who=enemy.name))
        return
    dmg = max(1, roll(enemy.attack, game.rng))
    data["hp"] = max(0, int(data.get("hp") or 0) - dmg)
    game.say(t(game.lang, "ally_hurt", name=name, who=enemy.name, dmg=dmg))
    if data["hp"] <= 0:
        game.say(t(game.lang, "ally_down", name=name))


def _allies_act(game: "Game", living: list[Fighter]) -> None:
    for fid, data in list((game.state.followers or {}).items()):
        if int(data.get("hp") or 0) <= 0:
            continue
        living[:] = [e for e in living if e.hp > 0]
        if not living:
            return
        target = living[0]
        name = game.npc_name(fid)
        to_hit = roll("1d20", game.rng) + 2
        ac = 10 + int(target.defense) + int(target.ac_bonus)
        if to_hit < ac:
            game.say(t(game.lang, "ally_miss", name=name))
            continue
        dmg = max(1, roll(data.get("attack") or "1d4", game.rng))
        target.hp -= dmg
        game.say(t(game.lang, "ally_hit", name=name, dmg=dmg, target=target.name))
        if target.hp <= 0:
            game.say(t(game.lang, "enemy_down", name=target.name))


def _status(game: "Game", living: list[Fighter]) -> None:
    p = game.state.player
    line = f"{t(game.lang, 'you_are')}  {t(game.lang, 'hp')} {p.hp}/{p.max_hp}"
    if p.max_mp:
        line += f"  {t(game.lang, 'mp')} {p.mp}/{p.max_mp}"
    lines = [line]
    for fid, data in (game.state.followers or {}).items():
        name = game.npc_name(fid)
        if int(data.get("hp") or 0) <= 0:
            lines.append(f"{name}  {t(game.lang, 'ally_down_short')}")
        else:
            lines.append(f"{name}  {t(game.lang, 'hp')} {data.get('hp')}/{data.get('max_hp')}")
    for e in living:
        lines.append(f"{e.name}  {t(game.lang, 'hp')} {e.hp}/{e.max_hp}")
    game.say("\n".join(lines))


def _cast(game: "Game", ability_id: str, living: list[Fighter]) -> bool:
    spec = (game.world.abilities or {}).get(ability_id) or {}
    cost = int(spec.get("mp") or 0)
    p = game.state.player
    if p.mp < cost:
        game.say(t(game.lang, "no_mp"))
        return False
    p.mp -= cost
    text = loc(spec.get("text"), game.lang)
    if text:
        game.say(text)
    target = _pick_target(game, living, "")
    if not target:
        return True
    bonus = player_attack_bonus(game) + int(spec.get("hit") or 0)
    to_hit = roll("1d20", game.rng) + bonus
    ac = 10 + int(target.defense) + int(target.ac_bonus)
    if spec.get("auto_hit"):
        to_hit = ac
    if to_hit < ac:
        game.say(t(game.lang, "you_miss"))
        return True
    expr = spec.get("damage") or (player_weapon(game).get("damage") or "1d4")
    dmg = roll(expr, game.rng) + int(spec.get("bonus") or 0)
    target.hp -= max(0, dmg)
    name = loc(spec.get("name") or ability_id, game.lang)
    game.say(t(game.lang, "you_hit", dmg=dmg, name=name))
    if spec.get("effects"):
        apply_effects(game, spec.get("effects"))
    if target.hp <= 0:
        game.say(t(game.lang, "enemy_down", name=target.name))
    return True


def _pick_target(game: "Game", living: list[Fighter], extra: str) -> Optional[Fighter]:
    if not living:
        return None
    if len(living) == 1:
        return living[0]
    if extra:
        q = extra.lower()
        for e in living:
            if q in e.name.lower() or q == e.id.lower():
                return e
        if extra.isdigit():
            i = int(extra) - 1
            if 0 <= i < len(living):
                return living[i]
    listing = ", ".join(f"{i+1}:{e.name}" for i, e in enumerate(living))
    game.say(t(game.lang, "pick_enemy", list=listing))
    raw = (game.ui.read(t(game.lang, "prompt")) or "").strip()
    if raw.isdigit():
        i = int(raw) - 1
        if 0 <= i < len(living):
            return living[i]
    q = raw.lower()
    for e in living:
        if q in e.name.lower():
            return e
    return living[0]


def _player_hit(game: "Game", target: Fighter) -> None:
    weapon = player_weapon(game)
    bonus = player_attack_bonus(game)
    to_hit = roll("1d20", game.rng) + bonus
    ac = 10 + int(target.defense) + int(target.ac_bonus)
    if to_hit < ac:
        game.say(t(game.lang, "you_miss"))
        return
    dmg = roll(weapon.get("damage") or "1d4", game.rng)
    if game.has_flag("demon_weak") and game.combat_id == "vargos":
        dmg += roll("1d6", game.rng)
    if game.has_flag("true_name_spoken") and game.combat_id == "vargos":
        dmg += 2
    target.hp -= dmg
    wname = loc(weapon.get("name"), game.lang)
    game.say(t(game.lang, "you_hit", dmg=dmg, name=wname or target.name))
    if target.hp <= 0:
        game.say(t(game.lang, "enemy_down", name=target.name))


def _enemy_hit(game: "Game", enemy: Fighter, ac: int) -> None:
    to_hit = roll("1d20", game.rng) + int(enemy.defense)
    if to_hit < ac:
        miss = loc((enemy.phrases or {}).get("miss"), game.lang)
        game.say(miss or t(game.lang, "miss", who=enemy.name))
        return
    dmg = max(0, roll(enemy.attack, game.rng))
    game.state.player.hp = max(0, game.state.player.hp - dmg)
    hit = loc((enemy.phrases or {}).get("hit"), game.lang)
    if hit:
        game.say(hit + f" (−{dmg})")
    else:
        game.say(t(game.lang, "hit", who=enemy.name, dmg=dmg, target=t(game.lang, "you_are")))


def _use_in_combat(game: "Game", extra: str, living: list[Fighter]) -> None:
    if not extra:
        names = []
        choices = []
        for iid in game.state.player.inventory:
            item = game.world.items.get(iid) or {}
            label = loc(item.get("name") or iid, game.lang)
            names.append(label)
            choices.append({"label": label, "command": iid})
        game.set_choices(choices + [{"label": t(game.lang, "gui_leave"), "command": "0"}])
        game.say(t(game.lang, "which_item", list=", ".join(names) or "—"))
        extra = (game.ui.read(t(game.lang, "prompt")) or "").strip()
        if extra in ("0", "leave", "уйти"):
            return
    if extra:
        game.use_item(extra, combat=True)


def _victory(game: "Game", enc: dict, enemies: list[Fighter]) -> None:
    lang = game.lang
    xp = int(enc.get("xp") or 0) + sum(e.xp for e in enemies)
    if xp:
        game.add_xp(xp)
    if enc.get("enemies"):
        loot = list(enc.get("loot") or [])
        for e in enemies:
            loot.extend(e.loot)
    else:
        loot = list(enc.get("loot") or [])
    from .loot import resolve_loot

    for drop in resolve_loot(game.world, loot):
        iid, chance = drop.get("item"), int(drop.get("chance") or 100)
        if not iid:
            continue
        if roll("1d100", game.rng) <= chance:
            if game.give_item(str(iid), silent=True):
                game.say(t(lang, "got_loot", name=game.item_name(str(iid))))
    game.state.defeated.add(enc.get("id") or game.combat_id)
