"""Game loop and command handlers."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Optional

from . import combat, dialogue, effects, save
from .conditions import check, skill_bonus
from .hooks import Hooks
from .i18n import dir_id, dir_name, t
from .loader import World, initial_location_items, initial_location_npcs, load_world
from .parser import parse
from .state import GameState, Player, StatusEffect, STAT_KEYS
from .ui import ScriptedIO, TerminalIO
from .clock import advance, clock, encounter_chance, phase_name, shop_is_open
from .audio import Audio
from .util import as_list, loc, match_entity, modifier, roll, wrap


class Game:
    def __init__(
        self,
        world: World,
        hooks: Optional[Hooks] = None,
        ui=None,
        language: str = "ru",
        seed: int = 1,
        ask_name: bool = True,
        player_class: Optional[str] = None,
    ):
        self.world = world
        self.hooks = hooks or Hooks(None)
        self.ui = ui or TerminalIO()
        self.running = True
        self.in_combat = False
        self.in_dialogue = False
        self.combat_id = ""
        self.last_skill_roll = (0, 0, False)
        self.ask_name = ask_name
        self.player_class = player_class or ""
        self.in_shop = False
        self.ui_choices: list = []
        self.state = self._new_state(language, seed)
        self.audio = Audio(world.path, world.game.get("audio"))
        if self.player_class:
            self.apply_class(self.player_class, silent=True)

    @property
    def lang(self) -> str:
        return self.state.language

    @property
    def rng(self):
        # consume one call counter so saves can restore sequence if needed
        self.state.rng_calls += 1
        return random.Random(self.state.rng_seed + self.state.rng_calls * 9973)

    def say(self, text: str) -> None:
        if text:
            self.ui.write(wrap(str(text)))

    def has_flag(self, name: str) -> bool:
        return name in self.state.flags

    def has_item(self, item_id: str) -> bool:
        return item_id in self.state.player.inventory

    def item_name(self, item_id: str) -> str:
        item = self.world.items.get(item_id) or {}
        return loc(item.get("name") or item_id, self.lang)

    def loc_name(self, loc_id: str) -> str:
        room = self.world.locations.get(loc_id) or {}
        return loc(room.get("name") or loc_id, self.lang)

    def npc_name(self, npc_id: str) -> str:
        npc = self.world.npcs.get(npc_id) or {}
        return loc(npc.get("name") or npc_id, self.lang)

    def set_choices(self, choices: list | None) -> None:
        self.ui_choices = list(choices or [])
        fn = getattr(self.ui, "set_choices", None)
        if callable(fn):
            fn(self.ui_choices)

    def snapshot(self) -> dict:
        """Button-friendly view of the current room. Safe to call from the UI thread."""
        p = self.state.player
        mode = "play"
        if self.state.ended:
            mode = "ended"
        elif self.in_combat:
            mode = "combat"
        elif self.in_shop:
            mode = "shop"
        elif self.in_dialogue:
            mode = "dialogue"
        elif self.ui_choices:
            mode = "prompt"
        exits = []
        for d, dest in self.visible_exits().items():
            exits.append(
                {
                    "id": d,
                    "label": dir_name(d, self.lang),
                    "locked": self.is_locked(d, dest),
                    "command": d,
                }
            )
        items = []
        for iid in self.state.location_items.get(self.state.location) or []:
            items.append({"id": iid, "label": self.item_name(iid), "command": f"take {iid}"})
        npcs = []
        for nid, data in self._here_npcs().items():
            npcs.append(
                {
                    "id": nid,
                    "label": self.npc_name(nid),
                    "talk": f"talk {nid}",
                    "attack": f"attack {nid}",
                    "shop": bool(data.get("shop")),
                }
            )
        containers = []
        for cid, box in (self.room().get("containers") or {}).items():
            if not isinstance(box, dict):
                box = {"name": cid}
            containers.append(
                {
                    "id": cid,
                    "label": loc(box.get("name") or cid, self.lang),
                    "command": f"open {cid}",
                }
            )
        inv = []
        eq = set((p.equipment or {}).values())
        for iid in p.inventory:
            item = self.world.items.get(iid) or {}
            inv.append(
                {
                    "id": iid,
                    "label": self.item_name(iid),
                    "equipped": iid in eq,
                    "type": item.get("type") or "misc",
                }
            )
        return {
            "mode": mode,
            "title": loc(self.world.title, self.lang),
            "location_id": self.state.location,
            "location": self.loc_name(self.state.location),
            "player": p.name,
            "hp": p.hp,
            "max_hp": p.max_hp,
            "mp": p.mp,
            "max_mp": p.max_mp,
            "gold": p.gold,
            "phase": clock(self)[1],
            "hour": clock(self)[0],
            "xp": p.xp,
            "level": p.level,
            "ended": self.state.ended,
            "dark": self.is_dark(),
            "exits": exits,
            "items": items,
            "npcs": npcs,
            "containers": containers,
            "inventory": inv,
            "choices": list(self.ui_choices),
            "can_rest": self.room().get("rest") is not False,
            "recipes": [
                {"id": rid, "label": loc(r.get("name") or rid, self.lang), "command": f"craft {rid}"}
                for rid, r in self.world.recipes.items()
                if (r.get("station") in (None, self.state.location))
                or self.state.location in (self.room().get("tags") or [])
                or r.get("station") in (self.room().get("tags") or [])
            ],
        }

    # ------------------------------------------------------------------ setup
    def _new_state(self, language: str, seed: int) -> GameState:
        g = self.world.game
        start = self.world.start_location
        if not start and self.world.locations:
            start = next(iter(self.world.locations))
        pdata = g.get("player") or {}
        stats = {k: 10 for k in STAT_KEYS}
        stats.update(pdata.get("stats") or {})
        raw_name = pdata.get("name")
        if isinstance(raw_name, dict):
            pname = loc(raw_name, language)
        elif raw_name:
            pname = str(raw_name)
        else:
            pname = loc({"ru": "Герой", "en": "Hero"}, language)
        player = Player(
            name=pname,
            stats=stats,
            hp=int(pdata.get("hp") or pdata.get("max_hp") or 20),
            max_hp=int(pdata.get("max_hp") or pdata.get("hp") or 20),
            mp=int(pdata.get("mp") or 0),
            max_mp=int(pdata.get("max_mp") or pdata.get("mp") or 0),
            gold=int(pdata.get("gold") or 0),
            xp=int(pdata.get("xp") or 0),
            level=int(pdata.get("level") or 1),
            inventory=list(pdata.get("inventory") or []),
            equipment=dict(pdata.get("equipment") or {}),
            skills=dict(pdata.get("skills") or g.get("skills") or {}),
        )
        state_rep = {}
        for fid, spec in (g.get("factions") or {}).items():
            start_rep = 0
            if isinstance(spec, dict) and spec.get("start") is not None:
                start_rep = int(spec.get("start") or 0)
            state_rep[str(fid)] = start_rep
        lang = language or g.get("language") or "ru"
        st = GameState(
            location=start,
            language=lang,
            rng_seed=int(seed),
            player=player,
            location_items=initial_location_items(self.world),
            location_npcs=initial_location_npcs(self.world),
            reputation=state_rep,
        )
        for qid, q in self.world.quests.items():
            if q.get("auto_start"):
                st.quests[qid] = "active"
        return st

    def start(self) -> str:
        """Run until quit. Returns ending: '', 'win', 'lose', 'quit'."""
        if self.world.errors:
            for e in self.world.errors:
                self.say(e)
            return "error"
        for w in self.world.warnings:
            pass  # silent in play; shown by `validate`
        self.hooks.call("on_load", self)
        title = loc(self.world.title, self.lang)
        self.say(title)
        intro = loc(self.world.game.get("intro"), self.lang)
        if intro:
            self.say("")
            self.say(intro)
        pdata = self.world.game.get("player") or {}
        if self.ask_name and pdata.get("name_prompt"):
            prompt = loc(
                pdata.get("name_prompt_text")
                or {"ru": "Твоё имя:", "en": "Your name:"},
                self.lang,
            )
            name = (self.ui.read(prompt + " ") or "").strip()
            if name and name.lower() not in ("quit", "выход"):
                self.state.player.name = name
        classes = self.world.game.get("classes") or {}
        prompt_class = self.world.game.get("class_prompt")
        if prompt_class is None:
            prompt_class = bool(classes)
        if classes and prompt_class and self.ask_name and not self.player_class:
            self._pick_class(classes)
        self._look(full=True, first=True)
        self.hooks.call("on_enter", self, self.state.location)
        self._fire_enter(self.state.location)
        while self.running and not self.state.ended:
            if not self.in_combat and not self.in_dialogue and not self.in_shop:
                self.set_choices([])
            line = self.ui.read(t(self.lang, "prompt"))
            self.handle(line)
            if self.running and not self.state.ended:
                self._check_ending()
            if self.running and not self.state.ended:
                self.hooks.call("on_turn", self)
                self._tick()
                self._check_ending()
        if self.state.ended == "win":
            self._show_ending("win")
        elif self.state.ended == "lose":
            self._show_ending("lose")
        else:
            self.say(t(self.lang, "bye"))
        return self.state.ended or "quit"

    def _pick_class(self, classes: dict) -> None:
        ids = list(classes)
        self.say(t(self.lang, "pick_class"))
        choices = []
        for i, cid in enumerate(ids, 1):
            spec = classes[cid] or {}
            label = loc(spec.get("name") or cid, self.lang)
            text = loc(spec.get("text") or spec.get("description"), self.lang)
            line = f"  {i}. {label}"
            if text:
                line += f" — {text}"
            self.say(line)
            choices.append({"label": f"{i}. {label}", "command": str(i)})
        self.set_choices(choices)
        raw = (self.ui.read(t(self.lang, "prompt")) or "").strip()
        self.set_choices([])
        picked = ""
        if raw.isdigit() and 1 <= int(raw) <= len(ids):
            picked = ids[int(raw) - 1]
        else:
            q = raw.lower()
            for cid, spec in classes.items():
                if q == cid.lower() or q in loc(spec.get("name") or "", self.lang).lower():
                    picked = cid
                    break
        if not picked:
            picked = ids[0]
        self.apply_class(picked)

    def apply_class(self, cid: str, silent: bool = False) -> None:
        spec = (self.world.game.get("classes") or {}).get(cid) or {}
        if not spec:
            return
        p = self.state.player
        if spec.get("stats"):
            p.stats.update({k: int(v) for k, v in spec["stats"].items()})
        if spec.get("hp") or spec.get("max_hp"):
            p.max_hp = int(spec.get("max_hp") or spec.get("hp") or p.max_hp)
            p.hp = int(spec.get("hp") or p.max_hp)
        if spec.get("mp") is not None:
            p.mp = p.max_mp = int(spec.get("max_mp") or spec.get("mp") or 0)
        if spec.get("gold") is not None:
            p.gold = int(spec["gold"])
        if spec.get("inventory") is not None:
            p.inventory = list(spec.get("inventory") or [])
        if spec.get("equipment") is not None:
            p.equipment = dict(spec.get("equipment") or {})
        if spec.get("skills"):
            p.skills.update(spec["skills"])
        self.player_class = cid
        self.state.flags.add(f"class_{cid}")
        if not silent:
            label = loc(spec.get("name") or cid, self.lang)
            self.say(t(self.lang, "class_set", name=label))

    def handle(self, line: str) -> None:
        cmd = parse(line)
        if cmd is None:
            return
        custom = self.hooks.call("on_command", self, cmd.verb, cmd.args)
        if custom:
            return
        handlers = {
            "look": self._cmd_look,
            "go": self._cmd_go,
            "take": self._cmd_take,
            "drop": self._cmd_drop,
            "use": self._cmd_use,
            "equip": self._cmd_equip,
            "unequip": self._cmd_unequip,
            "inventory": self._cmd_inv,
            "talk": self._cmd_talk,
            "attack": self._cmd_attack,
            "search": self._cmd_search,
            "open": self._cmd_open,
            "read": self._cmd_read,
            "give": self._cmd_give,
            "buy": self._cmd_buy,
            "sell": self._cmd_sell,
            "shop": self._cmd_shop,
            "craft": self._cmd_craft,
            "combine": self._cmd_combine,
            "stats": self._cmd_stats,
            "quests": self._cmd_quests,
            "journal": self._cmd_journal,
            "map": self._cmd_map,
            "rest": self._cmd_rest,
            "wait": self._cmd_wait,
            "party": self._cmd_party,
            "reputation": self._cmd_reputation,
            "save": self._cmd_save,
            "load": self._cmd_load,
            "help": self._cmd_help,
            "quit": self._cmd_quit,
            "language": self._cmd_lang,
            "say": self._cmd_say,
            "put": self._cmd_drop,
            "unknown": self._cmd_unknown,
        }
        fn = handlers.get(cmd.verb, self._cmd_unknown)
        fn(cmd)

    # ------------------------------------------------------------------ world helpers
    def room(self) -> dict:
        return self.world.locations.get(self.state.location) or {}

    def visible_exits(self) -> dict:
        room = self.room()
        exits = dict(room.get("exits") or {})
        revealed = set(self.state.revealed_exits.get(self.state.location) or [])
        out = {}
        for d, dest in exits.items():
            hidden = dest.get("hidden") if isinstance(dest, dict) else False
            if hidden and d not in revealed:
                continue
            out[d] = dest
        return out

    def exit_target(self, dest) -> str:
        if isinstance(dest, str):
            return dest
        return (dest or {}).get("to") or ""

    def is_locked(self, direction: str, dest) -> bool:
        if not isinstance(dest, dict):
            return False
        key = f"{self.state.location}:{direction}"
        if key in self.state.unlocked:
            return False
        if dest.get("locked"):
            return True
        if dest.get("lock_flag") and dest.get("lock_flag") not in self.state.flags:
            return True
        return False

    def is_dark(self) -> bool:
        if not self.room().get("dark"):
            return False
        for iid in self.state.player.inventory:
            item = self.world.items.get(iid) or {}
            if item.get("light"):
                return False
        return True

    def place_item(self, loc_id: str, item_id: str) -> None:
        self.state.location_items.setdefault(loc_id, []).append(item_id)

    def place_npc(self, loc_id: str, npc_id: str) -> None:
        lst = self.state.location_npcs.setdefault(loc_id, [])
        if npc_id not in lst:
            lst.append(npc_id)

    def add_follower(self, info) -> None:
        if isinstance(info, str):
            nid, spec = str(info), {}
        elif isinstance(info, dict):
            nid = str(info.get("npc") or info.get("id") or "")
            spec = info
        else:
            return
        if not nid or nid in self.state.followers:
            return
        if len(self.state.followers) >= self.party_max():
            self.say(t(self.lang, "party_full", n=self.party_max()))
            return
        npc = self.world.npcs.get(nid) or {}
        combat_spec = spec.get("combat") or npc.get("combat") or {}
        hp = int(combat_spec.get("hp") or spec.get("hp") or 8)
        self.state.followers[nid] = {
            "hp": hp,
            "max_hp": hp,
            "attack": str(combat_spec.get("attack") or spec.get("attack") or "1d4"),
            "ac": int(combat_spec.get("ac") or spec.get("ac") or 0),
            "cover": (combat_spec.get("cover") if "cover" in combat_spec else spec.get("cover", True)) is not False,
        }
        self.place_npc(self.state.location, nid)
        self.say(t(self.lang, "follows_now", name=self.npc_name(nid)))

    def remove_follower(self, npc_id: str) -> None:
        self.state.followers.pop(str(npc_id), None)

    def _bring_followers(self, loc_id: str) -> None:
        if not self.state.followers:
            return
        names = []
        for fid in list(self.state.followers):
            self.remove_npc(fid)
            self.place_npc(loc_id, fid)
            names.append(self.npc_name(fid))
        self.say(t(self.lang, "follows", names=", ".join(names)))

    def party_max(self) -> int:
        settings = self.world.game.get("settings") or {}
        raw = settings.get("party")
        if raw is None:
            raw = settings.get("party_max")
        if raw is None:
            raw = 4
        return max(1, int(raw))

    def change_rep(self, info) -> None:
        if not isinstance(info, dict):
            return
        for fid, delta in info.items():
            cur = int(self.state.reputation.get(str(fid), 0))
            self.state.reputation[str(fid)] = cur + int(delta)
            self.say(t(self.lang, "rep_change", name=self.faction_name(str(fid)), n=int(delta)))

    def set_rep(self, info) -> None:
        if not isinstance(info, dict):
            return
        for fid, value in info.items():
            self.state.reputation[str(fid)] = int(value)
            self.say(t(self.lang, "rep_set", name=self.faction_name(str(fid)), n=int(value)))

    def faction_name(self, fid: str) -> str:
        spec = (self.world.game.get("factions") or {}).get(fid) or {}
        return loc(spec.get("name") or fid, self.lang)

    def hunger_cfg(self) -> dict:
        raw = self.world.game.get("hunger") or {}
        return raw if isinstance(raw, dict) and raw.get("max") else {}

    def _hunger_tick(self) -> None:
        cfg = self.hunger_cfg()
        if not cfg or self.state.ended:
            return
        step = int(cfg.get("step") or 1)
        mx = int(cfg.get("max") or 10)
        self.state.hunger = min(mx, int(self.state.hunger) + max(0, step))
        if self.state.hunger >= mx:
            dmg = int(cfg.get("damage") or 1)
            if dmg:
                self.state.player.hp = max(0, self.state.player.hp - dmg)
                self.say(t(self.lang, "hungry", n=dmg))
                if self.state.player.hp <= 0:
                    self.say(t(self.lang, "starved"))
                    self.finish("lose")

    def sate(self, amount: int) -> None:
        if not self.hunger_cfg() or not amount:
            return
        self.state.hunger = max(0, int(self.state.hunger) - int(amount))
        self.say(t(self.lang, "sated", n=self.state.hunger))

    def remove_npc(self, npc_id: str) -> None:
        for loc_id, npcs in self.state.location_npcs.items():
            if npc_id in npcs:
                npcs.remove(npc_id)

    def give_item(self, item_id: str, silent: bool = True) -> bool:
        settings = self.world.game.get("settings") or {}
        inv = self.state.player.inventory
        limit = settings.get("inventory_limit")
        if limit and len(inv) >= int(limit):
            if not silent:
                self.say(t(self.lang, "inv_full"))
            return False
        wlim = settings.get("weight_limit")
        if wlim:
            w = self._weight() + int((self.world.items.get(item_id) or {}).get("weight") or 0)
            if w > int(wlim):
                if not silent:
                    self.say(t(self.lang, "too_heavy"))
                return False
        inv.append(item_id)
        if not silent:
            self.say(t(self.lang, "taken", name=self.item_name(item_id)))
        return True

    def take_from_inv(self, item_id: str, silent: bool = False) -> bool:
        inv = self.state.player.inventory
        if item_id not in inv:
            return False
        inv.remove(item_id)
        eq = self.state.player.equipment
        for slot, iid in list(eq.items()):
            if iid == item_id:
                eq.pop(slot, None)
        if not silent:
            self.say(t(self.lang, "dropped", name=self.item_name(item_id)))
        return True

    def _weight(self) -> int:
        total = 0
        for iid in self.state.player.inventory:
            total += int((self.world.items.get(iid) or {}).get("weight") or 0)
        return total

    def add_xp(self, amount: int) -> None:
        if not amount:
            return
        p = self.state.player
        p.xp += amount
        self.say(t(self.lang, "got_xp", xp=amount))
        # simple curve: 50, 120, 210, ...
        while p.xp >= self._xp_needed(p.level):
            p.level += 1
            p.max_hp += 4
            p.hp = p.max_hp
            self.say(t(self.lang, "level_up", level=p.level))

    def _xp_needed(self, level: int) -> int:
        return 40 * level * (level + 1) // 2

    def move_to(self, loc_id: str, silent: bool = False) -> None:
        if loc_id not in self.world.locations:
            return
        old = self.state.location
        self.hooks.call("on_leave", self, old)
        self.state.location = loc_id
        self._bring_followers(loc_id)
        if not silent:
            self._look(full=True)
        self.hooks.call("on_enter", self, loc_id)
        self._fire_enter(loc_id)
        self._hunger_tick()
        music = (self.world.locations.get(loc_id) or {}).get("music")
        if music:
            self.audio.play_music(str(music))

    def start_combat(self, encounter_id: str) -> str:
        return combat.run(self, encounter_id)

    def finish(self, ending: str) -> None:
        if self.state.ended:
            return
        self.state.ended = ending
        self.running = False

    def tick_status(self, in_combat: bool = False) -> None:
        p = self.state.player
        remain = []
        for s in p.status:
            if not isinstance(s, StatusEffect):
                continue
            if s.dot:
                p.hp = max(0, p.hp - int(s.dot))
                self.say(t(self.lang, "poison_tick", n=s.dot))
                if p.hp <= 0:
                    self.finish("lose")
            s.turns -= 1
            if s.turns > 0:
                remain.append(s)
            else:
                self.say(t(self.lang, "effect_end", name=loc(s.name, self.lang)))
        p.status = remain

    def _tick(self) -> None:
        self.state.time += 1
        self.tick_status()
        self._fire_events("turn")

    def _fire_enter(self, loc_id: str) -> None:
        first = loc_id not in self.state.visited
        self.state.visited.add(loc_id)
        room = self.world.locations.get(loc_id) or {}
        if first:
            fv = loc(room.get("first_visit"), self.lang)
            if fv:
                self.say(fv)
            effects.apply(self, room.get("on_first_enter"))
        effects.apply(self, room.get("on_enter"))
        self._fire_events("enter")
        # random encounter
        table = room.get("random_encounters")
        if table and not self.state.ended and not self.in_combat:
            key = f"renc:{loc_id}"
            if table.get("once") and key in self.state.once:
                pass
            else:
                chance = encounter_chance(self, table)
                if roll("1d100", self.rng) <= chance:
                    from .loot import pick_encounter

                    pick = pick_encounter(table, self.rng)
                    enc = (pick or {}).get("encounter") if pick else None
                    if enc:
                        once_key = f"renc:{loc_id}:{enc}"
                        if pick.get("once") and once_key in self.state.once:
                            pass
                        else:
                            self.state.once.add(key)
                            self.state.once.add(once_key)
                            self.start_combat(str(enc))

    def _fire_events(self, kind: str) -> None:
        for ev in self.world.events:
            eid = ev.get("id") or ""
            if ev.get("once") and eid in self.state.once:
                continue
            when = ev.get("when") or {}
            trigger = ev.get("trigger") or when.get("on") or "enter"
            if kind == "enter" and trigger not in ("enter", "any", None):
                if when.get("enter") and when.get("enter") != self.state.location:
                    continue
                if trigger not in ("enter", "move"):
                    if "enter" not in when and trigger != "enter":
                        # events without trigger fire on enter if they have enter: loc
                        if "enter" not in when:
                            continue
            if kind == "turn" and trigger not in ("turn", "any"):
                continue
            if kind == "enter":
                enter_loc = when.get("enter")
                if enter_loc and enter_loc != self.state.location:
                    continue
            if not check(self, when):
                continue
            if ev.get("once") or ev.get("id"):
                if ev.get("once"):
                    self.state.once.add(eid)
            effects.apply(self, ev.get("effects"))
            if self.state.ended:
                return

    def _check_ending(self) -> None:
        if self.state.ended:
            return
        if self._ending_matches(self.world.game.get("win") or {}):
            self.finish("win")
            return
        if self._ending_matches(self.world.game.get("lose") or {}):
            self.finish("lose")

    def _ending_matches(self, block: dict) -> bool:
        if not block:
            return False
        if block.get("when"):
            return check(self, block["when"])
        flags = as_list(block.get("flags"))
        if flags:
            return all(f in self.state.flags for f in flags)
        if block.get("flag"):
            return block.get("flag") in self.state.flags
        return False

    def _show_ending(self, kind: str) -> None:
        block = self.world.game.get(kind) or {}
        banner = t(self.lang, "win" if kind == "win" else "lose")
        self.say("")
        self.say(banner)
        text = loc(block.get("text"), self.lang)
        if kind == "win" and self.has_flag("dark_pact") and not self.has_flag("demon_slain"):
            text = loc(block.get("pact_text") or text, self.lang)
        if text:
            self.say(text)
        self.hooks.call("on_ending", self, kind)

    def use_item(self, query: str, combat: bool = False) -> None:
        iid = self._match_inv(query)
        if not iid:
            self.say(t(self.lang, "no_item"))
            return
        item = self.world.items.get(iid) or {}
        handled = self.hooks.call("on_use_item", self, iid, None)
        if handled:
            return
        use = item.get("use") or {}
        if item.get("type") == "consumable" or use:
            if use.get("when") and not check(self, use["when"]):
                self.say(t(self.lang, "cant_use"))
                return
            text = loc(use.get("text") or item.get("use_text"), self.lang)
            if text:
                self.say(text)
            else:
                self.say(t(self.lang, "used", name=self.item_name(iid)))
            if "heal" in item and "heal" not in (use.get("effects") or {}):
                effects.apply(self, {"heal": item.get("heal")})
            effects.apply(self, use.get("effects"))
            sate = item.get("sates", use.get("sates") if isinstance(use, dict) else None)
            if sate:
                self.sate(int(sate))
            if use.get("consume", item.get("type") == "consumable"):
                self.take_from_inv(iid, silent=True)
            return
        if item.get("type") in ("weapon", "armor", "shield", "accessory"):
            self._equip_id(iid)
            return
        self.say(t(self.lang, "cant_use"))

    # ------------------------------------------------------------------ matching
    def _here_items(self) -> dict:
        ids = list(self.state.location_items.get(self.state.location) or [])
        found = self.state.hidden_found.get(self.state.location) or []
        ids.extend(found)
        return {i: self.world.items.get(i) or {"id": i, "name": i} for i in ids}

    def _here_npcs(self) -> dict:
        ids = list(self.state.location_npcs.get(self.state.location) or [])
        out = {}
        for n in ids:
            if n in self.state.defeated:
                continue
            out[n] = self.world.npcs.get(n) or {"id": n, "name": n}
        return out

    def _here_containers(self) -> dict:
        room = self.room()
        return dict(room.get("containers") or {})

    def _match_inv(self, query: str) -> Optional[str]:
        entities = {
            i: self.world.items.get(i) or {"id": i, "name": i}
            for i in self.state.player.inventory
        }
        return match_entity(query, entities, self.lang)

    def _match_here_item(self, query: str) -> Optional[str]:
        return match_entity(query, self._here_items(), self.lang)

    def _match_npc(self, query: str) -> Optional[str]:
        return match_entity(query, self._here_npcs(), self.lang)

    def _match_any_item(self, query: str) -> Optional[str]:
        return match_entity(query, self.world.items, self.lang)

    # ------------------------------------------------------------------ look
    def _look(self, full: bool = True, first: bool = False, target: str = "") -> None:
        if target:
            self._examine(target)
            return
        if self.is_dark():
            self._header()
            self.say(t(self.lang, "dark"))
            exits = self.visible_exits()
            names = [dir_name(d, self.lang) for d in exits]
            if names:
                self.say(f"{t(self.lang, 'exits')}: {', '.join(names)}")
            return
        room = self.room()
        self._header()
        phase = clock(self)[1]
        alt = room.get(f"description_{phase}")
        desc = loc(alt if alt else room.get("description"), self.lang)
        note = loc(room.get(f"note_{phase}"), self.lang)
        if note:
            desc = f"{desc}\n{note}".strip() if desc else note
        if desc:
            self.say(desc)
        extras = []
        items = self.state.location_items.get(self.state.location) or []
        if items:
            extras.append(
                f"{t(self.lang, 'items_here')}: {', '.join(self.item_name(i) for i in items)}"
            )
        npcs = []
        for n in (self.state.location_npcs.get(self.state.location) or []):
            if n in self.state.defeated:
                continue
            label = self.npc_name(n)
            if n in self.state.followers:
                down = int((self.state.followers[n] or {}).get("hp") or 0) <= 0
                label += f" ({t(self.lang, 'with_you_down' if down else 'with_you')})"
            npcs.append(label)
        if npcs:
            extras.append(f"{t(self.lang, 'people_here')}: {', '.join(npcs)}")
        cons = []
        for cid, c in (room.get("containers") or {}).items():
            cons.append(loc(c.get("name") or cid, self.lang))
        if cons:
            extras.append(f"{t(self.lang, 'containers')}: {', '.join(cons)}")
        exits = self.visible_exits()
        bits = []
        for d, dest in exits.items():
            label = dir_name(d, self.lang)
            if self.is_locked(d, dest):
                label += f" ({t(self.lang, 'locked')})"
            bits.append(label)
        if bits:
            extras.append(f"{t(self.lang, 'exits')}: {', '.join(bits)}")
        if extras:
            self.say("")
            self.say("\n".join(extras))

    def _header(self) -> None:
        p = self.state.player
        room = self.room()
        title = loc(room.get("name") or self.state.location, self.lang).upper()
        bar = f"{title}    {t(self.lang, 'hp')} {p.hp}/{p.max_hp}"
        if p.max_mp:
            bar += f"  {t(self.lang, 'mp')} {p.mp}/{p.max_mp}"
        bar += f"  {t(self.lang, 'gold')} {p.gold}"
        bar += f"  {phase_name(self)}"
        if self.hunger_cfg():
            mx = int(self.hunger_cfg().get("max") or 0)
            bar += f"  {t(self.lang, 'hunger')} {self.state.hunger}/{mx}"
        self.say("")
        self.say(bar)
        self.say("-" * min(72, max(24, len(bar))))

    def _examine(self, query: str) -> None:
        iid = self._match_here_item(query) or self._match_inv(query)
        if iid:
            item = self.world.items.get(iid) or {}
            self.say(loc(item.get("description") or item.get("name") or iid, self.lang))
            return
        nid = self._match_npc(query)
        if nid:
            npc = self.world.npcs.get(nid) or {}
            self.say(loc(npc.get("description") or npc.get("name") or nid, self.lang))
            return
        # room feature
        feats = self.room().get("features") or {}
        hit = match_entity(query, {k: (v if isinstance(v, dict) else {"name": k, "description": v}) for k, v in feats.items()}, self.lang)
        if hit:
            feat = feats[hit]
            if isinstance(feat, dict):
                self.say(loc(feat.get("description") or feat.get("text"), self.lang) or t(self.lang, "nothing"))
                effects.apply(self, feat.get("on_examine"))
            else:
                self.say(loc(feat, self.lang))
            return
        d = dir_id(query)
        if d and d in self.visible_exits():
            dest = self.visible_exits()[d]
            if isinstance(dest, dict) and dest.get("description"):
                self.say(loc(dest.get("description"), self.lang))
                return
        self.say(t(self.lang, "nothing"))

    # ------------------------------------------------------------------ commands
    def _cmd_look(self, cmd) -> None:
        self._look(target=cmd.argstr)

    def _cmd_go(self, cmd) -> None:
        direction = cmd.direction or (dir_id(cmd.argstr) if cmd.argstr else None)
        if not direction:
            self.say(t(self.lang, "dirs"))
            return
        exits = self.visible_exits()
        if direction not in exits:
            self.say(t(self.lang, "no_exit"))
            return
        dest = exits[direction]
        target = self.exit_target(dest)
        dest_d = dest if isinstance(dest, dict) else {}
        if dest_d.get("when") and not check(self, dest_d.get("when")):
            self.say(loc(dest_d.get("blocked_text"), self.lang) or t(self.lang, "no_exit"))
            return
        if self.is_locked(direction, dest):
            key = dest_d.get("key")
            if key and self.has_item(str(key)):
                self.state.unlocked.add(f"{self.state.location}:{direction}")
                self.say(t(self.lang, "unlocked"))
            else:
                self.say(loc(dest_d.get("locked_text"), self.lang) or t(self.lang, "need_key"))
                return
        # str/skill break
        if dest_d.get("break"):
            spec = dest_d["break"]
            if check(self, spec.get("when") or spec):
                pass
        trap = dest_d.get("trap")
        if trap and f"trap:{self.state.location}:{direction}" not in self.state.once:
            skill = trap.get("skill") or "dex"
            dc = int(trap.get("dc") or 12)
            total = roll("1d20", self.rng) + skill_bonus(self, skill)
            if total >= dc:
                self.say(loc(trap.get("text_success"), self.lang) or t(self.lang, "skill_ok", roll=total, dc=dc))
            else:
                self.say(loc(trap.get("text_fail"), self.lang) or t(self.lang, "skill_fail", roll=total, dc=dc))
                effects.apply(self, trap.get("effects") or ({"damage": trap.get("damage")} if trap.get("damage") else []))
            if trap.get("once", True):
                self.state.once.add(f"trap:{self.state.location}:{direction}")
            if self.state.ended:
                return
        effects.apply(self, dest_d.get("on_use"))
        if self.state.ended:
            return
        self.move_to(target)

    def _cmd_take(self, cmd) -> None:
        if not cmd.argstr:
            self.say(t(self.lang, "what"))
            return
        if cmd.argstr in ("all", "всё", "все"):
            for iid in list(self.state.location_items.get(self.state.location) or []):
                self._take_one(iid)
            return
        iid = self._match_here_item(cmd.argstr)
        if not iid:
            self.say(t(self.lang, "gone"))
            return
        self._take_one(iid)

    def _take_one(self, iid: str) -> None:
        item = self.world.items.get(iid) or {}
        if item.get("takeable") is False:
            self.say(t(self.lang, "cant_take"))
            return
        loc_items = self.state.location_items.setdefault(self.state.location, [])
        hidden = self.state.hidden_found.setdefault(self.state.location, [])
        if iid in loc_items:
            loc_items.remove(iid)
        elif iid in hidden:
            hidden.remove(iid)
        else:
            self.say(t(self.lang, "gone"))
            return
        if not self.give_item(iid, silent=False):
            loc_items.append(iid)

    def _cmd_drop(self, cmd) -> None:
        if not cmd.argstr:
            self.say(t(self.lang, "what"))
            return
        iid = self._match_inv(cmd.argstr)
        if not iid:
            self.say(t(self.lang, "no_item"))
            return
        self.take_from_inv(iid, silent=False)
        self.place_item(self.state.location, iid)

    def _cmd_use(self, cmd) -> None:
        if not cmd.argstr:
            self.say(t(self.lang, "what"))
            return
        self.use_item(cmd.argstr)

    def _cmd_equip(self, cmd) -> None:
        if not cmd.argstr:
            self.say(t(self.lang, "what"))
            return
        iid = self._match_inv(cmd.argstr)
        if not iid:
            self.say(t(self.lang, "no_item"))
            return
        self._equip_id(iid)

    def _equip_id(self, iid: str) -> None:
        item = self.world.items.get(iid) or {}
        slot = item.get("slot") or {"weapon": "weapon", "armor": "armor", "shield": "shield"}.get(item.get("type"))
        if not slot:
            self.say(t(self.lang, "cant_equip"))
            return
        self.state.player.equipment[slot] = iid
        self.say(t(self.lang, "equip_ok", name=self.item_name(iid)))

    def _cmd_unequip(self, cmd) -> None:
        if not cmd.argstr:
            self.state.player.equipment.clear()
            self.say(t(self.lang, "unequip_ok", name="*"))
            return
        iid = self._match_inv(cmd.argstr)
        if not iid:
            self.say(t(self.lang, "no_item"))
            return
        eq = self.state.player.equipment
        for slot, v in list(eq.items()):
            if v == iid:
                eq.pop(slot)
                self.say(t(self.lang, "unequip_ok", name=self.item_name(iid)))
                return
        self.say(t(self.lang, "cant_equip"))

    def _cmd_inv(self, cmd) -> None:
        inv = self.state.player.inventory
        self.say(t(self.lang, "inventory"))
        if not inv:
            self.say(t(self.lang, "empty_inv"))
            return
        eq_ids = set(self.state.player.equipment.values())
        for iid in inv:
            mark = f" ({t(self.lang, 'equipped')})" if iid in eq_ids else ""
            self.say(f"  - {self.item_name(iid)}{mark}")

    def _cmd_talk(self, cmd) -> None:
        npcs = self._here_npcs()
        if not npcs:
            self.say(t(self.lang, "talk_nobody"))
            return
        nid = None
        if cmd.argstr:
            nid = self._match_npc(cmd.argstr)
        elif len(npcs) == 1:
            nid = next(iter(npcs))
        if not nid:
            self.say(t(self.lang, "who"))
            return
        dialogue.run(self, nid)

    def _cmd_attack(self, cmd) -> None:
        npcs = self._here_npcs()
        nid = self._match_npc(cmd.argstr) if cmd.argstr else (next(iter(npcs)) if len(npcs) == 1 else None)
        if nid:
            npc = self.world.npcs.get(nid) or {}
            enc = npc.get("encounter") or nid
            if enc in self.world.encounters or npc.get("hostile"):
                result = self.start_combat(enc if enc in self.world.encounters else nid)
                if result == "win":
                    self.state.defeated.add(nid)
                    self.remove_npc(nid)
                    effects.apply(self, npc.get("on_death"))
                return
            self.say(loc(npc.get("attack_text"), self.lang) or t(self.lang, "nothing_happens"))
            return
        # room encounter leftover
        room = self.room()
        if room.get("encounter") and room.get("encounter") not in self.state.defeated:
            self.start_combat(room["encounter"])
            return
        self.say(t(self.lang, "no_target"))

    def _cmd_search(self, cmd) -> None:
        room = self.room()
        spec = room.get("search") or {}
        dc = int(spec.get("dc") or 0)
        ok = True
        if dc:
            total = roll("1d20", self.rng) + skill_bonus(self, spec.get("skill") or "perception")
            ok = total >= dc
            self.say(t(self.lang, "skill_ok" if ok else "skill_fail", roll=total, dc=dc))
        if not ok:
            self.say(t(self.lang, "search_fail"))
            return
        revealed = []
        for iid in room.get("_hidden_ids") or as_list(spec.get("reveal") or spec.get("reveal_items")):
            found = self.state.hidden_found.setdefault(self.state.location, [])
            loc_items = self.state.location_items.setdefault(self.state.location, [])
            if iid in found or iid in loc_items or iid in self.state.player.inventory:
                continue
            loc_items.append(iid)
            revealed.append(iid)
        text = loc(spec.get("text") or spec.get("success"), self.lang)
        if text:
            self.say(text)
        elif revealed:
            self.say(t(self.lang, "search_ok"))
            for iid in revealed:
                self.say("  " + self.item_name(iid))
        else:
            self.say(t(self.lang, "search_fail"))
        if ok:
            effects.apply(self, spec.get("effects") or spec.get("success_effects"))
            if spec.get("reveal_exit"):
                effects.apply(self, {"reveal_exit": spec.get("reveal_exit")})

    def _cmd_open(self, cmd) -> None:
        if not cmd.argstr:
            self.say(t(self.lang, "what"))
            return
        cons = self._here_containers()
        cid = match_entity(
            cmd.argstr,
            {k: (v if isinstance(v, dict) else {"name": k}) for k, v in cons.items()},
            self.lang,
        )
        if not cid:
            # maybe locked exit
            d = dir_id(cmd.argstr)
            if d and d in self.visible_exits():
                fake = type("C", (), {"direction": d, "argstr": d, "args": [d], "raw": cmd.raw, "verb": "go"})()
                self._cmd_go(fake)
                return
            self.say(t(self.lang, "gone"))
            return
        box = cons[cid] if isinstance(cons[cid], dict) else {}
        key_id = f"{self.state.location}:{cid}"
        if key_id in self.state.opened:
            self.say(t(self.lang, "nothing"))
            return
        if box.get("locked"):
            need = box.get("key")
            if need and not self.has_item(str(need)):
                # skill lockpick
                lk = box.get("lockpick")
                if lk:
                    dc = int(lk if not isinstance(lk, dict) else lk.get("dc", 12))
                    total = roll("1d20", self.rng) + skill_bonus(self, "lockpick")
                    if total < dc:
                        self.say(t(self.lang, "need_lockpick"))
                        return
                    self.say(t(self.lang, "broke_lock"))
                else:
                    self.say(loc(box.get("locked_text"), self.lang) or t(self.lang, "need_key"))
                    return
        self.state.opened.add(key_id)
        self.say(t(self.lang, "opened", name=loc(box.get("name") or cid, self.lang)))
        for iid in as_list(box.get("items") or box.get("contains")):
            self.place_item(self.state.location, str(iid))
            self.say("  " + self.item_name(str(iid)))
        if box.get("gold"):
            effects.apply(self, {"give_gold": box.get("gold")})
        effects.apply(self, box.get("effects"))

    def _cmd_read(self, cmd) -> None:
        q = cmd.argstr
        iid = (self._match_inv(q) if q else None) or (self._match_here_item(q) if q else None)
        if not iid:
            # any readable in inv
            for hid in self.state.player.inventory:
                item = self.world.items.get(hid) or {}
                if item.get("text") or item.get("type") == "book":
                    iid = hid
                    break
        if not iid:
            self.say(t(self.lang, "no_read"))
            return
        item = self.world.items.get(iid) or {}
        text = loc(item.get("text") or item.get("description"), self.lang)
        self.say(t(self.lang, "read", name=self.item_name(iid), text=text or t(self.lang, "nothing")))
        effects.apply(self, item.get("on_read"))

    def _cmd_give(self, cmd) -> None:
        parts = cmd.args
        if len(parts) < 1:
            self.say(t(self.lang, "what"))
            return
        # give ITEM to NPC / give NPC ITEM
        iid = self._match_inv(" ".join(parts))
        nid = None
        if not iid and len(parts) >= 2:
            for i in range(1, len(parts)):
                maybe_item = self._match_inv(" ".join(parts[:i]))
                maybe_npc = self._match_npc(" ".join(parts[i:]))
                if maybe_item and maybe_npc:
                    iid, nid = maybe_item, maybe_npc
                    break
                maybe_npc = self._match_npc(" ".join(parts[:i]))
                maybe_item = self._match_inv(" ".join(parts[i:]))
                if maybe_item and maybe_npc:
                    iid, nid = maybe_item, maybe_npc
                    break
        if not nid:
            npcs = self._here_npcs()
            if len(npcs) == 1:
                nid = next(iter(npcs))
                iid = iid or self._match_inv(" ".join(parts))
        if not iid or not nid:
            self.say(t(self.lang, "what"))
            return
        npc = self.world.npcs.get(nid) or {}
        wants = as_list(npc.get("wants") or [])
        self.take_from_inv(iid, silent=False)
        self.say(t(self.lang, "gave", name=self.item_name(iid)))
        if iid in wants or not wants:
            effects.apply(self, npc.get("on_give"))
            if isinstance(npc.get("on_give_item"), dict):
                effects.apply(self, npc["on_give_item"].get(iid))

    def _cmd_shop(self, cmd) -> None:
        npcs = self._here_npcs()
        nid = None
        if cmd.argstr:
            nid = self._match_npc(cmd.argstr)
        else:
            for n, data in npcs.items():
                if data.get("shop"):
                    nid = n
                    break
        if not nid:
            self.say(t(self.lang, "gone"))
            return
        open_shop(self, nid)

    def _cmd_buy(self, cmd) -> None:
        npcs = [n for n, d in self._here_npcs().items() if d.get("shop")]
        if not npcs:
            self.say(t(self.lang, "gone"))
            return
        open_shop(self, npcs[0], preset=f"buy {cmd.argstr}".strip())

    def _cmd_sell(self, cmd) -> None:
        npcs = [n for n, d in self._here_npcs().items() if d.get("shop")]
        if not npcs:
            self.say(t(self.lang, "gone"))
            return
        open_shop(self, npcs[0], preset=f"sell {cmd.argstr}".strip())

    def _cmd_craft(self, cmd) -> None:
        if not cmd.argstr:
            names = [loc(r.get("name") or rid, self.lang) for rid, r in self.world.recipes.items()]
            self.say(t(self.lang, "what") + " " + ", ".join(names))
            return
        rid = match_entity(cmd.argstr, self.world.recipes, self.lang)
        if not rid:
            self.say(t(self.lang, "no_recipe"))
            return
        rec = self.world.recipes[rid]
        station = rec.get("station")
        if station and self.state.location != station and station not in self.room().get("stations", []):
            if station not in (self.room().get("tags") or []):
                # allow if station is a location id mismatch - still try tags
                if rec.get("station") not in (self.room().get("tags") or []) and rec.get("station") != self.state.location:
                    self.say(t(self.lang, "cant_use"))
                    return
        ings = [str(x) for x in as_list(rec.get("ingredients"))]
        inv = list(self.state.player.inventory)
        for ing in ings:
            if ing not in inv:
                self.say(t(self.lang, "craft_fail"))
                return
            inv.remove(ing)
        for ing in ings:
            self.take_from_inv(ing, silent=True)
        result = str(rec.get("result") or rid)
        self.give_item(result, silent=True)
        self.say(loc(rec.get("text"), self.lang) or t(self.lang, "craft_ok", name=self.item_name(result)))
        effects.apply(self, rec.get("effects"))

    def _cmd_combine(self, cmd) -> None:
        # combine a and b
        raw = cmd.argstr.replace(" и ", " ").replace(" and ", " ").replace("+", " ")
        tokens = raw.split()
        if len(tokens) < 2:
            self.say(t(self.lang, "what"))
            return
        a = self._match_inv(tokens[0])
        b = self._match_inv(" ".join(tokens[1:])) or self._match_inv(tokens[-1])
        if not a or not b:
            self.say(t(self.lang, "no_item"))
            return
        for iid in (a, b):
            item = self.world.items.get(iid) or {}
            combo = item.get("combine") or {}
            others = [str(x) for x in as_list(combo.get("with"))]
            if (a if iid == b else b) in others:
                result = str(combo.get("result"))
                self.take_from_inv(a, silent=True)
                self.take_from_inv(b, silent=True)
                self.give_item(result, silent=True)
                self.say(t(self.lang, "combined", name=self.item_name(result)))
                effects.apply(self, combo.get("effects"))
                return
        self.say(t(self.lang, "cant_combine"))

    def _cmd_stats(self, cmd) -> None:
        p = self.state.player
        self.say(f"{p.name}  {t(self.lang, 'level')} {p.level}  {t(self.lang, 'xp')} {p.xp}")
        self.say(f"{t(self.lang, 'hp')} {p.hp}/{p.max_hp}   {t(self.lang, 'gold')} {p.gold}")
        parts = [f"{k.upper()} {v}({modifier(int(v)):+d})" for k, v in p.stats.items()]
        self.say("  ".join(parts))
        w = p.equipment.get("weapon")
        a = p.equipment.get("armor")
        if w:
            self.say(f"{t(self.lang, 'weapon')}: {self.item_name(w)}")
        if a:
            self.say(f"{t(self.lang, 'armor')}: {self.item_name(a)}")
        self.say(f"{t(self.lang, 'ac')}: {combat.player_ac(self)}")
        if p.status:
            names = [loc(getattr(s, "name", s), self.lang) for s in p.status]
            self.say(f"{t(self.lang, 'status')}: {', '.join(names)}")

    def _cmd_quests(self, cmd) -> None:
        self.say(t(self.lang, "quests"))
        if not self.state.quests:
            self.say(t(self.lang, "no_quests"))
            return
        for qid, status in self.state.quests.items():
            q = self.world.quests.get(qid) or {}
            name = loc(q.get("name") or qid, self.lang)
            key = {"active": "quest_active", "done": "quest_done", "failed": "quest_failed"}.get(status, status)
            self.say(f"  - {name} [{t(self.lang, key)}]")
            desc = loc(q.get("description"), self.lang)
            if desc and status == "active":
                self.say(f"    {desc}")

    def _cmd_journal(self, cmd) -> None:
        self.say(t(self.lang, "journal"))
        if not self.state.journal:
            self.say(t(self.lang, "nothing"))
            return
        for line in self.state.journal:
            self.say(f"  - {line}")

    def known_exits(self, loc_id: str) -> list[tuple[str, str, bool]]:
        room = self.world.locations.get(loc_id) or {}
        revealed = set(self.state.revealed_exits.get(loc_id) or [])
        out = []
        for direction, dest in (room.get("exits") or {}).items():
            hidden = dest.get("hidden") if isinstance(dest, dict) else False
            if hidden and direction not in revealed:
                continue
            target = self.exit_target(dest)
            locked = False
            if isinstance(dest, dict):
                key = f"{loc_id}:{direction}"
                if key not in self.state.unlocked:
                    if dest.get("locked") or (
                        dest.get("lock_flag") and dest.get("lock_flag") not in self.state.flags
                    ):
                        locked = True
            out.append((direction, target, locked))
        return out

    def _visit_order(self) -> list[str]:
        visited = set(self.state.visited)
        start = self.state.location if self.state.location in visited else ""
        order: list[str] = []
        seen: set[str] = set()
        queue = [start] if start else []
        while queue:
            loc_id = queue.pop(0)
            if not loc_id or loc_id in seen or loc_id not in visited:
                continue
            seen.add(loc_id)
            order.append(loc_id)
            for _d, target, _locked in self.known_exits(loc_id):
                if target in visited and target not in seen:
                    queue.append(target)
        for loc_id in sorted(visited):
            if loc_id not in seen:
                order.append(loc_id)
        return order

    def _cmd_map(self, cmd) -> None:
        self.say(t(self.lang, "map"))
        if not self.state.visited:
            self.say(t(self.lang, "nothing"))
            return
        for loc_id in self._visit_order():
            mark = "*" if loc_id == self.state.location else " "
            self.say(f"{mark} {self.loc_name(loc_id)}")
            for direction, target, locked in self.known_exits(loc_id):
                if target and target in self.state.visited:
                    dest = self.loc_name(target)
                else:
                    dest = "?"
                if locked:
                    dest += f" ({t(self.lang, 'locked')})"
                self.say(f"    {dir_name(direction, self.lang)} — {dest}")

    def _cmd_party(self, cmd) -> None:
        self.say(t(self.lang, "party"))
        if not self.state.followers:
            self.say(t(self.lang, "party_empty"))
            return
        for fid, data in self.state.followers.items():
            name = self.npc_name(fid)
            if int(data.get("hp") or 0) <= 0:
                self.say(f"  {name}  {t(self.lang, 'ally_down_short')}")
            else:
                self.say(f"  {name}  {t(self.lang, 'hp')} {data.get('hp')}/{data.get('max_hp')}")

    def _cmd_reputation(self, cmd) -> None:
        self.say(t(self.lang, "reputation"))
        factions = self.world.game.get("factions") or {}
        keys = list(factions) or list(self.state.reputation)
        if not keys:
            self.say(t(self.lang, "nothing"))
            return
        for fid in keys:
            n = int(self.state.reputation.get(str(fid), 0))
            self.say(f"  {self.faction_name(str(fid))}: {n}")

    def _cmd_rest(self, cmd) -> None:
        room = self.room()
        if room.get("rest") is False:
            self.say(t(self.lang, "cant_rest"))
            return
        npcs = self._here_npcs()
        hostile = any((self.world.npcs.get(n) or {}).get("hostile") for n in npcs)
        if hostile:
            self.say(t(self.lang, "cant_rest"))
            return
        effects.apply(self, {"rest": True})
        effects.apply(self, room.get("on_rest"))
        down = [
            self.npc_name(fid)
            for fid, data in self.state.followers.items()
            if int(data.get("hp") or 0) <= 0
        ]
        for data in self.state.followers.values():
            data["hp"] = data.get("max_hp") or data.get("hp") or 8
        if down:
            self.say(t(self.lang, "ally_up", names=", ".join(down)))
        cfg = self.hunger_cfg()
        if cfg:
            self.state.hunger = int(cfg.get("rest") if cfg.get("rest") is not None else 0)
        advance(self)
        self.say(t(self.lang, "time_shift", phase=phase_name(self)))

    def _cmd_wait(self, cmd) -> None:
        self.say(t(self.lang, "wait"))
        self._hunger_tick()

    def _cmd_save(self, cmd) -> None:
        slot = cmd.argstr or "slot1"
        save.write_save(self.world.path, slot, self.state)
        self.say(t(self.lang, "saved", slot=slot))

    def _cmd_load(self, cmd) -> None:
        slot = cmd.argstr or "slot1"
        try:
            data = save.read_save(self.world.path, slot)
        except FileNotFoundError:
            self.say(t(self.lang, "no_save"))
            return
        self.state = GameState.from_dict(data)
        self.say(t(self.lang, "loaded", slot=slot))
        self._look(full=True)

    def _cmd_help(self, cmd) -> None:
        self.say(t(self.lang, "help_title"))
        self.say(t(self.lang, "help_body"))

    def _cmd_quit(self, cmd) -> None:
        self.running = False

    def _cmd_lang(self, cmd) -> None:
        arg = (cmd.argstr or "").lower()
        if arg in ("ru", "рус", "russian", "русский"):
            self.state.language = "ru"
        elif arg in ("en", "eng", "english", "английский"):
            self.state.language = "en"
        else:
            self.state.language = "en" if self.state.language == "ru" else "ru"
        self.say(t(self.lang, "lang_set"))

    def _cmd_say(self, cmd) -> None:
        if not cmd.argstr:
            self.say(t(self.lang, "say_what"))
            return
        handled = self.hooks.call("on_command", self, "say", cmd.args)
        if not handled:
            self.say(t(self.lang, "nothing_happens"))

    def _cmd_unknown(self, cmd) -> None:
        # try direction fallback
        if cmd.args:
            d = dir_id(cmd.args[0])
            if d:
                cmd.direction = d
                cmd.verb = "go"
                self._cmd_go(cmd)
                return
        self.say(t(self.lang, "unknown"))


def open_shop(game: Game, npc_id: str, preset: str = "") -> None:
    npc = game.world.npcs.get(npc_id) or {}
    if not shop_is_open(game, npc):
        game.say(t(game.lang, "shop_closed", phase=phase_name(game)))
        return
    stock_src = npc.get("shop") or []
    key = npc_id
    game.in_shop = True
    if key not in game.state.shop_stock:
        game.state.shop_stock[key] = []
        for row in stock_src:
            if isinstance(row, str):
                item = game.world.items.get(row) or {}
                game.state.shop_stock[key].append(
                    {"item": row, "price": int(item.get("value") or 5), "stock": 3}
                )
            elif isinstance(row, dict):
                game.state.shop_stock[key].append(
                    {
                        "item": row.get("item") or row.get("id"),
                        "price": int(row.get("price") or row.get("value") or 5),
                        "stock": int(row.get("stock") if row.get("stock") is not None else 3),
                    }
                )
    game.say(t(game.lang, "shop") + " — " + game.npc_name(npc_id))
    game.say(t(game.lang, "shop_hint"))

    def show():
        rows = game.state.shop_stock.get(key) or []
        if not rows:
            game.say(t(game.lang, "shop_empty"))
            return
        for row in rows:
            if row.get("stock", 1) == 0:
                continue
            name = game.item_name(row["item"])
            game.say(f"  {name} — {row['price']} ({row.get('stock', 1)})")

    def shop_choices():
        ch = []
        for row in game.state.shop_stock.get(key) or []:
            if int(row.get("stock", 1)) == 0:
                continue
            name = game.item_name(row["item"])
            ch.append(
                {
                    "label": f"{name} — {row['price']}",
                    "command": f"buy {row['item']}",
                }
            )
        ch.append({"label": t(game.lang, "gui_leave"), "command": "leave"})
        game.set_choices(ch)

    show()
    commands = [preset] if preset else []
    try:
        while True:
            if commands:
                raw = commands.pop(0)
            else:
                shop_choices()
                raw = (game.ui.read(t(game.lang, "prompt")) or "").strip()
            if not raw:
                continue
            low = raw.lower()
            if low in ("leave", "уйти", "выход", "quit", "0", "back"):
                game.say(t(game.lang, "left"))
                return
            parts = low.split(None, 1)
            verb, rest = parts[0], parts[1] if len(parts) > 1 else ""
            if verb in ("list", "смотреть", "look", "список"):
                show()
                continue
            if verb in ("buy", "купить"):
                row = _shop_match(game, key, rest)
                if not row:
                    game.say(t(game.lang, "gone"))
                    continue
                price = int(row["price"])
                if game.state.player.gold < price:
                    game.say(t(game.lang, "not_enough_gold"))
                    continue
                if int(row.get("stock", 1)) == 0:
                    game.say(t(game.lang, "shop_empty"))
                    continue
                game.state.player.gold -= price
                game.give_item(row["item"], silent=True)
                if int(row.get("stock", 1)) > 0:
                    row["stock"] = int(row["stock"]) - 1
                game.say(t(game.lang, "bought", name=game.item_name(row["item"]), n=price))
                if preset:
                    return
                continue
            if verb in ("sell", "продать"):
                iid = game._match_inv(rest)
                if not iid:
                    game.say(t(game.lang, "no_item"))
                    continue
                item = game.world.items.get(iid) or {}
                price = max(1, int(item.get("value") or 1) // 2)
                game.take_from_inv(iid, silent=True)
                game.state.player.gold += price
                game.say(t(game.lang, "sold", name=game.item_name(iid), n=price))
                if preset:
                    return
                continue
            game.say(t(game.lang, "shop_hint"))
            if preset:
                return
    finally:
        game.in_shop = False
        game.set_choices([])


def _shop_match(game: Game, key: str, query: str) -> Optional[dict]:
    rows = game.state.shop_stock.get(key) or []
    entities = {}
    for i, row in enumerate(rows):
        src = dict(game.world.items.get(row["item"]) or {})
        src["id"] = row["item"]
        entities[row["item"]] = src
    hit = match_entity(query, entities, game.lang)
    if not hit:
        return None
    for row in rows:
        if row["item"] == hit:
            return row
    return None


def play_path(
    game_dir: str | Path,
    language: str = "ru",
    seed: int = 1,
    ui=None,
    ask_name: bool = True,
) -> Game:
    world = load_world(game_dir)
    hooks = Hooks.load(Path(game_dir))
    game = Game(world, hooks=hooks, ui=ui, language=language, seed=seed, ask_name=ask_name)
    game.start()
    return game
