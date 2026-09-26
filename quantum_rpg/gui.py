"""Minimal Tk window: log + action buttons + command line. No graphics."""

from __future__ import annotations

import threading
from .tclfix import prepare

prepare()
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
from typing import Callable, Optional

from . import __version__
from .engine import Game
from .hooks import Hooks
from .i18n import t
from .loader import load_world
from .paths import games_dir, list_games
from .save import list_slots
from .theme import C, Btn, font_ui, font_log
from .ui import QueueIO
from .util import loc


def launch_gui(language: str = "ru") -> None:
    root = tk.Tk()
    root.configure(bg=C["bg"])
    root.title(f"Quantum Text RPG {__version__}")
    try:
        root.iconname("QuantumRPG")
    except Exception:
        pass
    Launcher(root, language=language)
    root.mainloop()


class Launcher:
    def __init__(self, root: tk.Tk, language: str = "ru"):
        self.root = root
        self.lang = language
        self.frame = tk.Frame(root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)
        root.geometry("560x540")
        root.minsize(480, 440)
        self._build()
        self._refresh_games()

    def _tr(self, key: str) -> str:
        return t(self.lang, key)

    def _build(self) -> None:
        pad = tk.Frame(self.frame, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)
        tk.Label(
            pad, text="QUANTUM TEXT RPG", bg=C["bg"], fg=C["accent"],
            font=font_ui(16, True),
        ).pack(anchor="w")
        tk.Label(
            pad, text=self._tr("gui_subtitle"), bg=C["bg"], fg=C["dim"],
            font=font_ui(10),
        ).pack(anchor="w", pady=(4, 16))
        tk.Label(
            pad, text=self._tr("gui_games"), bg=C["bg"], fg=C["dim"],
            font=font_ui(9),
        ).pack(anchor="w")
        box = tk.Frame(pad, bg=C["line"])
        box.pack(fill="both", expand=True, pady=(4, 12))
        self.listbox = tk.Listbox(
            box, bg=C["panel"], fg=C["fg"], selectbackground=C["accent"],
            selectforeground=C["bg"], relief="flat", bd=0, font=font_ui(11),
            highlightthickness=0, activestyle="none",
        )
        self.listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self.listbox.bind("<Double-Button-1>", lambda e: self._play())
        row = tk.Frame(pad, bg=C["bg"])
        row.pack(fill="x")
        Btn(row, text=self._tr("gui_play"), command=self._play, anchor="center",
             font=font_ui(10, True), padx=16).pack(side="left")
        Btn(row, text=self._tr("ed_open"), command=self._edit, anchor="center").pack(side="left", padx=8)
        Btn(row, text=self._tr("ed_new"), command=self._new, anchor="center").pack(side="left")
        row2 = tk.Frame(pad, bg=C["bg"])
        row2.pack(fill="x", pady=(8, 0))
        Btn(row2, text=self._tr("gui_open"), command=self._open, anchor="center").pack(side="left")
        self.lang_btn = Btn(row2, text=self.lang.upper(), command=self._toggle_lang, anchor="center", width=4)
        self.lang_btn.pack(side="left", padx=8)
        Btn(row2, text=self._tr("gui_quit"), command=self.root.destroy, anchor="center").pack(side="right")
        tk.Label(
            pad, text=self._tr("gui_hint"), bg=C["bg"], fg=C["dim"],
            font=font_ui(8), wraplength=460, justify="left",
        ).pack(anchor="w", pady=(16, 0))
        self.paths: list[Path] = []

    def _refresh_games(self) -> None:
        self.listbox.delete(0, "end")
        self.paths = list_games()
        for p in self.paths:
            try:
                w = load_world(p)
                world_title = loc(w.title, self.lang)
            except Exception:
                world_title = p.name
            self.listbox.insert("end", f"  {world_title}")
        if self.paths:
            self.listbox.selection_set(0)

    def _toggle_lang(self) -> None:
        self.lang = "en" if self.lang == "ru" else "ru"
        self.frame.destroy()
        self.frame = tk.Frame(self.root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)
        self._build()
        self._refresh_games()

    def _selected(self) -> Optional[Path]:
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self.paths[sel[0]]

    def _open(self) -> None:
        path = filedialog.askdirectory(title=self._tr("gui_open"))
        if not path:
            return
        p = Path(path)
        if not (p / "game.yaml").exists():
            messagebox.showerror("Quantum RPG", "game.yaml not found")
            return
        self._start_play(p)

    def _play(self) -> None:
        p = self._selected()
        if not p:
            messagebox.showinfo("Quantum RPG", self._tr("gui_pick_game"))
            return
        self._start_play(p)

    def _start_play(self, path: Path) -> None:
        self.frame.pack_forget()
        PlayWindow(self.root, path, self.lang, on_exit=self._back)

    def _edit(self) -> None:
        p = self._selected()
        if not p:
            messagebox.showinfo("Quantum RPG", self._tr("gui_pick_game"))
            return
        self._start_edit(p)

    def _new(self) -> None:
        name = simpledialog.askstring("Quantum RPG", self._tr("ed_new_name"), parent=self.root)
        if not name:
            return
        from .project import new_game

        template = games_dir() / "template"
        try:
            dest = new_game(name, template)
        except FileExistsError as exc:
            messagebox.showerror("Quantum RPG", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Quantum RPG", str(exc))
            return
        self._refresh_games()
        self._start_edit(dest)

    def _start_edit(self, path: Path) -> None:
        from .editor import EditorWindow

        self.frame.pack_forget()
        EditorWindow(self.root, path, self.lang, on_exit=self._back)

    def _back(self) -> None:
        self.frame.pack(fill="both", expand=True)
        self._refresh_games()


class PlayWindow:
    def __init__(self, root: tk.Tk, game_path: Path, lang: str, on_exit: Callable, start_at: str = ""):
        self.root = root
        self.game_path = Path(game_path)
        self.lang = lang
        self.on_exit = on_exit
        self.ui = QueueIO()
        self.waiting = False
        self.snap: dict = {}
        self.selected_item: Optional[str] = None
        self.inv_tab = "all"
        world = load_world(self.game_path)
        if world.errors:
            messagebox.showerror("Quantum RPG", "\n".join(world.errors))
            on_exit()
            return
        self.game = Game(
            world,
            hooks=Hooks.load(self.game_path),
            ui=self.ui,
            language=lang,
            seed=1,
            ask_name=not bool(start_at),
            start_at=start_at,
        )
        self.ui.game = self.game
        root.geometry("1040x680")
        root.minsize(860, 560)
        self.frame = tk.Frame(root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)
        self._build()
        self.thread = threading.Thread(target=self._run_game, daemon=True)
        self.thread.start()
        self.root.after(40, self._pump)

    def _tr(self, key: str) -> str:
        return t(self.lang, key)

    def _run_game(self) -> None:
        try:
            self.game.start()
        finally:
            self.ui.out.put({"op": "ended", "text": "", "snap": self.ui._snap()})

    def _build(self) -> None:
        top = tk.Frame(self.frame, bg=C["panel"], height=40)
        top.pack(fill="x")
        top.pack_propagate(False)
        self.title_lbl = tk.Label(top, text="", bg=C["panel"], fg=C["accent"], font=font_ui(11, True))
        self.title_lbl.pack(side="left", padx=12)
        Btn(top, text=self._tr("gui_quit"), command=self._quit_game, anchor="center").pack(side="right", padx=8, pady=6)
        Btn(top, text=self._tr("gui_menu"), command=self._to_menu, anchor="center").pack(side="right", pady=6)
        Btn(top, text=self._tr("gui_load"), command=self._load, anchor="center").pack(side="right", padx=4, pady=6)
        Btn(top, text=self._tr("gui_save"), command=self._save, anchor="center").pack(side="right", pady=6)
        self.lang_btn = Btn(top, text=self.lang.upper(), command=self._toggle_lang, anchor="center", width=4)
        self.lang_btn.pack(side="right", padx=8, pady=6)

        self.status = tk.Label(self.frame, text="", bg=C["bg"], fg=C["fg"], font=font_ui(10), anchor="w")
        self.status.pack(fill="x", padx=12, pady=(8, 4))

        body = tk.Frame(self.frame, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=4)

        left = tk.Frame(body, bg=C["line"])
        left.pack(side="left", fill="both", expand=True)
        self.log = tk.Text(
            left, bg=C["panel"], fg=C["fg"], insertbackground=C["fg"],
            relief="flat", bd=0, wrap="word", font=font_log(11),
            highlightthickness=0, padx=12, pady=10, state="disabled",
        )
        scroll = tk.Scrollbar(left, command=self.log.yview, bg=C["panel"], troughcolor=C["bg"],
                              relief="flat", bd=0, width=10)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True, padx=1, pady=1)
        for name, color in (
            ("fg", C["fg"]),
            ("dim", C["dim"]),
            ("accent", C["accent"]),
            ("danger", C["danger"]),
            ("ok", C["ok"]),
        ):
            self.log.tag_configure(name, foreground=color)

        right_wrap = tk.Frame(body, bg=C["bg"], width=280)
        right_wrap.pack(side="right", fill="y", padx=(10, 0))
        right_wrap.pack_propagate(False)
        self.side_canvas = tk.Canvas(right_wrap, bg=C["bg"], highlightthickness=0, bd=0)
        self.side_scroll = tk.Scrollbar(right_wrap, command=self.side_canvas.yview, width=8, bg=C["bg"])
        self.side = tk.Frame(self.side_canvas, bg=C["bg"])
        self.side.bind("<Configure>", lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all")))
        self.side_canvas.create_window((0, 0), window=self.side, anchor="nw", width=262)
        self.side_canvas.configure(yscrollcommand=self.side_scroll.set)
        self.side_canvas.pack(side="left", fill="both", expand=True)
        self.side_scroll.pack(side="right", fill="y")
        self.side_canvas.bind_all("<MouseWheel>", self._on_wheel)

        bottom = tk.Frame(self.frame, bg=C["panel"])
        bottom.pack(fill="x", padx=12, pady=(4, 12))
        self.prompt_lbl = tk.Label(bottom, text=">", bg=C["panel"], fg=C["accent"], font=font_ui(11, True))
        self.prompt_lbl.pack(side="left", padx=(8, 4), pady=8)
        self.entry = tk.Entry(
            bottom, bg=C["bg"], fg=C["fg"], insertbackground=C["accent"],
            relief="flat", font=font_log(11), highlightthickness=1,
            highlightcolor=C["accent"], highlightbackground=C["line"],
        )
        self.entry.pack(side="left", fill="x", expand=True, pady=8, ipady=4)
        self.entry.bind("<Return>", lambda e: self._submit())
        Btn(bottom, text=self._tr("gui_send"), command=self._submit, anchor="center",
             font=font_ui(10, True)).pack(side="right", padx=8, pady=8)
        self.entry.focus_set()

    def _on_wheel(self, event) -> None:
        self.side_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _append(self, text: str, color: str = "") -> None:
        if not text:
            return
        self.log.configure(state="normal")
        tag = color if color in ("fg", "dim", "accent", "danger", "ok") else "fg"
        self.log.insert("end", text.rstrip() + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _reveal(self, text: str, color: str, anim: str, delay: int) -> None:
        if not text:
            return
        if anim not in ("type", "slow") or delay <= 0:
            self._append(text, color)
            return
        tag = color if color in ("fg", "dim", "accent", "danger", "ok") else "fg"
        step = max(12, min(int(delay), 70))
        parts = text.split(" ") if anim == "slow" else list(text)
        self.log.configure(state="normal")
        self.log.insert("end", "\n", tag)
        mark = f"anim{self.log.index('end').replace('.', '_')}"
        self.log.mark_set(mark, "end-1c")
        self.log.mark_gravity(mark, "right")
        self.log.configure(state="disabled")

        def tick(i: int = 0) -> None:
            if not self.frame.winfo_exists() or i >= len(parts):
                return
            piece = parts[i] if anim == "type" else ((" " if i else "") + parts[i])
            self.log.configure(state="normal")
            self.log.insert(mark, piece, tag)
            self.log.see("end")
            self.log.configure(state="disabled")
            self.root.after(step, lambda n=i + 1: tick(n))

        tick()

    def _screen(self, key: str) -> dict:
        return ((self.snap or {}).get("ui_screens") or {}).get(key) or {}

    def _shown(self, key: str, default: list[str]) -> list[str]:
        show = self._screen(key).get("show") or []
        return show or list(default)

    def _pump(self) -> None:
        if not self.frame.winfo_exists():
            return
        try:
            while True:
                msg = self.ui.out.get_nowait()
                op = msg.get("op")
                if op == "write":
                    self._append(msg.get("text") or "")
                elif op == "fx":
                    self._reveal(
                        msg.get("text") or "",
                        msg.get("color") or "fg",
                        msg.get("anim") or "",
                        int(msg.get("delay") or 0),
                    )
                elif op == "read":
                    self.waiting = True
                    prompt = (msg.get("prompt") or "> ").strip()
                    self.prompt_lbl.configure(text=prompt or ">")
                elif op == "choices":
                    pass
                elif op == "ended":
                    self.waiting = False
                    self._append("")
                snap = msg.get("snap")
                if snap:
                    self.snap = snap
                    self.lang = self.game.lang
                    self._render_side()
                    self._render_status()
        except Exception:
            pass
        if self.frame.winfo_exists():
            self.root.after(40, self._pump)

    def _render_status(self) -> None:
        s = self.snap or {}
        locn = (s.get("location") or "").upper()
        hp = f"{t(self.lang, 'hp')} {s.get('hp', 0)}/{s.get('max_hp', 0)}"
        gold = f"{t(self.lang, 'gold')} {s.get('gold', 0)}"
        phase = s.get("phase")
        when = f"  {t(self.lang, 'phase_' + phase)}" if phase else ""
        extra = ""
        if s.get("max_mp"):
            extra = f"  {t(self.lang, 'mp')} {s.get('mp')}/{s.get('max_mp')}"
        self.status.configure(text=f"{locn}    {hp}{extra}    {gold}{when}")
        self.title_lbl.configure(text=s.get("title") or "Quantum RPG")
        self.lang_btn.configure(text=self.lang.upper())

    def _clear_side(self) -> None:
        for w in self.side.winfo_children():
            w.destroy()

    def _head(self, text: str) -> None:
        tk.Label(self.side, text=text.upper(), bg=C["bg"], fg=C["dim"], font=font_ui(8), anchor="w").pack(
            fill="x", pady=(10, 2)
        )

    def _btn(self, label: str, cmd: str, dim: bool = False) -> None:
        fg = C["dim"] if dim else C["fg"]
        Btn(self.side, text=label, fg=fg, command=lambda c=cmd: self._send(c)).pack(fill="x", pady=1)

    def _ui_title(self, key: str, fallback: str) -> str:
        return ((self.snap or {}).get("ui_titles") or {}).get(key) or fallback

    def _render_side(self) -> None:
        self._clear_side()
        s = self.snap or {}
        mode = s.get("mode") or "play"
        choices = s.get("choices") or []
        if mode in ("combat", "dialogue", "shop", "prompt") and choices:
            title = {
                "combat": self._ui_title("combat", t(self.lang, "combat")),
                "dialogue": self._ui_title("dialogue", t(self.lang, "people_here")),
                "shop": self._ui_title("shop", t(self.lang, "shop")),
                "prompt": self._ui_title("prompt", t(self.lang, "pick_class")),
            }.get(mode, "")
            self._head(title)
            hint = self._screen(mode).get("hint") or ""
            if hint:
                tk.Label(self.side, text=hint, bg=C["bg"], fg=C["dim"], font=font_ui(8), anchor="w", wraplength=250).pack(fill="x")
            shown = self._shown(mode, ["gold", "goods", "sell"] if mode == "shop" else ["choices"])
            if mode == "shop" and "gold" in shown:
                tk.Label(
                    self.side,
                    text=f"{t(self.lang, 'gold')} {s.get('gold', 0)}",
                    bg=C["bg"], fg=C["accent"], font=font_ui(9), anchor="w",
                ).pack(fill="x")
            if "goods" in shown or mode != "shop":
                for ch in choices:
                    self._btn(ch.get("label") or ch.get("command"), ch.get("command") or "")
            if mode == "shop" and "sell" in shown:
                self._head(self._ui_title("inventory", t(self.lang, "inventory")))
                for it in s.get("inventory") or []:
                    self._btn(f"{self._tr('gui_sell')}: {it['label']}", f"sell {it['id']}")
            return

        panels = s.get("panels") or [
            "map", "meters", "exits", "people", "items", "containers", "roads", "actions", "party", "inventory"
        ]
        draw = {
            "map": self._panel_map,
            "meters": self._panel_meters,
            "exits": self._panel_exits,
            "people": self._panel_people,
            "items": self._panel_items,
            "containers": self._panel_containers,
            "roads": self._panel_roads,
            "actions": self._panel_actions,
            "party": self._panel_party,
            "inventory": self._panel_inventory,
        }
        for name in panels:
            fn = draw.get(str(name))
            if fn:
                fn(s)

    def _panel_map(self, s: dict) -> None:
        grid = s.get("grid") or []
        if not grid:
            return
        self._head(self._ui_title("map", t(self.lang, "map")))
        drawn = s.get("grid_text") or ""
        if drawn:
            tk.Label(
                self.side, text=drawn, bg=C["bg"], fg=C["fg"], font=font_log(8),
                justify="left", anchor="w",
            ).pack(anchor="w", pady=(0, 4))
        for row in grid:
            line = tk.Frame(self.side, bg=C["line"])
            line.pack(fill="x", pady=1)
            for cell in row:
                label = cell.get("label") or " "
                cmd = cell.get("command") or ""
                if cmd:
                    Btn(
                        line, text=label, command=lambda c=cmd: self._send(c),
                        font=font_log(9), anchor="center", width=max(4, len(label)),
                        fg=C["accent"] if cell.get("here") else C["fg"],
                    ).pack(side="left", padx=1, expand=True, fill="x")
                else:
                    tk.Label(
                        line, text=label or " ", bg=C["panel"], fg=C["accent"] if cell.get("here") else C["dim"],
                        font=font_log(9), width=4, anchor="center",
                    ).pack(side="left", padx=1, expand=True, fill="x")

    def _panel_meters(self, s: dict) -> None:
        rows = list(s.get("meters") or [])
        if s.get("hunger_max"):
            pass
        if not rows:
            return
        self._head(self._ui_title("meters", t(self.lang, "meters")))
        for row in rows:
            tk.Label(
                self.side,
                text=f"{row['label']}  {row.get('bar') or ''}  {row['value']}/{row['max']}",
                bg=C["bg"], fg=C["danger"] if row.get("warn") else C["fg"], font=font_log(9), anchor="w",
            ).pack(fill="x")

    def _panel_exits(self, s: dict) -> None:
        self._head(self._ui_title("exits", t(self.lang, "exits")))
        for ex in s.get("exits") or []:
            label = ex["label"]
            if ex.get("locked"):
                label = f"{label} ({t(self.lang, 'locked')})"
            self._btn(label, ex["command"], dim=bool(ex.get("locked")))

    def _panel_people(self, s: dict) -> None:
        if not s.get("npcs"):
            return
        self._head(self._ui_title("people", t(self.lang, "people_here")))
        for n in s["npcs"]:
            self._btn(f"{self._tr('gui_talk')}: {n['label']}", n["talk"])
            if n.get("shop"):
                self._btn(f"{t(self.lang, 'shop')}: {n['label']}", f"shop {n['id']}")
            self._btn(f"{self._tr('gui_attack')}: {n['label']}", n["attack"], dim=True)

    def _panel_items(self, s: dict) -> None:
        if not s.get("items"):
            return
        self._head(self._ui_title("items", t(self.lang, "items_here")))
        for it in s["items"]:
            self._btn(f"{self._tr('gui_take')}: {it['label']}", it["command"])

    def _panel_containers(self, s: dict) -> None:
        if not s.get("containers"):
            return
        self._head(self._ui_title("containers", t(self.lang, "containers")))
        for c in s["containers"]:
            self._btn(f"{self._tr('gui_open_c')}: {c['label']}", c["command"])

    def _panel_roads(self, s: dict) -> None:
        if not s.get("roads"):
            return
        self._head(self._ui_title("roads", t(self.lang, "roads")))
        for road in s["roads"]:
            self._btn(road["label"], road["command"])

    def _panel_actions(self, s: dict) -> None:
        self._head(self._ui_title("actions", self._tr("gui_actions")))
        for act in s.get("ui_actions") or []:
            self._btn(act.get("label") or act.get("command"), act.get("command") or "")
        self._btn(self._tr("gui_look"), "look")
        self._btn(self._tr("gui_search"), "search")
        self._btn(t(self.lang, "stats"), "stats")
        self._btn(t(self.lang, "quests"), "quests")
        self._btn(t(self.lang, "journal"), "journal")
        self._btn(t(self.lang, "map"), "map")
        self._btn(t(self.lang, "notes"), "note")
        self._btn(self._tr("ed_validate"), "check")
        self._btn(t(self.lang, "meters"), "meters")
        self._btn(t(self.lang, "party"), "party")
        self._btn(t(self.lang, "reputation"), "reputation")
        self._btn(t(self.lang, "sound_btn"), "sound")
        if s.get("can_rest"):
            self._btn(self._tr("gui_rest"), "rest")
        for rec in s.get("recipes") or []:
            self._btn(f"{self._tr('gui_craft')}: {rec['label']}", rec["command"])

    def _panel_party(self, s: dict) -> None:
        people = s.get("followers") or []
        if not people:
            return
        shown = self._shown("party", ["hp", "orders"])
        self._head(self._ui_title("party", t(self.lang, "party")))
        hint = self._screen("party").get("hint") or ""
        if hint:
            tk.Label(self.side, text=hint, bg=C["bg"], fg=C["dim"], font=font_ui(8), anchor="w", wraplength=250).pack(fill="x")
        for person in people:
            line = person["label"]
            if "hp" in shown:
                line += f"  {person.get('hp')}/{person.get('max_hp')}  {person.get('order')}"
            tk.Label(self.side, text=line, bg=C["bg"], fg=C["fg"], font=font_ui(9), anchor="w").pack(fill="x")
            if "orders" in shown:
                self._btn(t(self.lang, "order_wait_btn"), f"приказ {person['id']} жди")
                self._btn(t(self.lang, "order_follow_btn"), f"приказ {person['id']} за мной")
                self._btn(t(self.lang, "order_hold_btn"), f"приказ {person['id']} не дерись")

    def _panel_inventory(self, s: dict) -> None:
        self._head(self._ui_title("inventory", t(self.lang, "inventory")))
        inv = s.get("inventory") or []
        if not inv:
            tk.Label(self.side, text=t(self.lang, "empty_inv"), bg=C["bg"], fg=C["dim"],
                     font=font_ui(9), anchor="w").pack(fill="x")
            return
        kinds = []
        for it in inv:
            kind = it.get("type") or "misc"
            if kind not in kinds:
                kinds.append(kind)
        if self.inv_tab not in kinds and self.inv_tab != "all":
            self.inv_tab = "all"
        tabs = tk.Frame(self.side, bg=C["bg"])
        tabs.pack(fill="x", pady=(0, 4))
        self._inv_tab(tabs, "all", t(self.lang, "cat_all"))
        for kind in kinds:
            self._inv_tab(tabs, kind, t(self.lang, f"cat_{kind}"))
        shown = [it for it in inv if self.inv_tab == "all" or (it.get("type") or "misc") == self.inv_tab]
        for it in shown:
            mark = " *" if it.get("equipped") else ""
            self._btn(it["label"] + mark, f"__inv:{it['id']}")
        if self.selected_item:
            row = tk.Frame(self.side, bg=C["bg"])
            row.pack(fill="x", pady=4)
            for key, cmd in (
                ("gui_examine", f"look {self.selected_item}"),
                ("gui_use", f"use {self.selected_item}"),
                ("gui_equip", f"equip {self.selected_item}"),
                ("gui_drop", f"drop {self.selected_item}"),
            ):
                Btn(row, text=self._tr(key), command=lambda c=cmd: self._send(c),
                     font=font_ui(8), padx=4).pack(side="left", padx=1)

    def _inv_tab(self, parent, kind: str, label: str) -> None:
        on = self.inv_tab == kind
        tk.Button(
            parent, text=label, command=lambda k=kind: self._set_inv_tab(k),
            bg=C["line"] if on else C["btn"], fg=C["fg"],
            activebackground=C["line"], activeforeground=C["fg"],
            relief="flat", bd=0, padx=6, pady=2, font=font_ui(8, on),
            highlightthickness=0, cursor="hand2",
        ).pack(side="left", padx=(0, 3), pady=1)

    def _set_inv_tab(self, kind: str) -> None:
        self.inv_tab = kind
        self._render_side()

    def _send(self, command: str) -> None:
        if command.startswith("__inv:"):
            self.selected_item = command.split(":", 1)[1]
            self._render_side()
            return
        self._submit(command)

    def _submit(self, text: Optional[str] = None) -> None:
        if text is None:
            text = self.entry.get()
            self.entry.delete(0, "end")
        text = (text or "").strip()
        if not text:
            return
        self._append(f"> {text}")
        self.waiting = False
        self.ui.submit(text)

    def _save(self) -> None:
        slot = simpledialog.askstring("Quantum RPG", self._tr("gui_slot"), parent=self.root) or "slot1"
        self._submit(f"save {slot}")

    def _load(self) -> None:
        slots = list_slots(self.game_path)
        slot = simpledialog.askstring(
            "Quantum RPG",
            self._tr("gui_slot") + (("  " + ", ".join(slots)) if slots else "  (" + self._tr("gui_no_saves") + ")"),
            parent=self.root,
        )
        if slot:
            self._submit(f"load {slot}")

    def _toggle_lang(self) -> None:
        self._submit("language")

    def _quit_game(self) -> None:
        self.ui.submit("quit")
        self.root.after(200, self._close)

    def _to_menu(self) -> None:
        self.ui.submit("quit")
        self.root.after(200, self._close)

    def _close(self) -> None:
        try:
            self.ui.close()
        except Exception:
            pass
        try:
            self.root.unbind_all("<MouseWheel>")
        except Exception:
            pass
        self.frame.destroy()
        self.on_exit()
