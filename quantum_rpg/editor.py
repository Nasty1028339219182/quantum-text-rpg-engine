"""YAML game editor — forms for the main files, text for events/hooks."""

from __future__ import annotations

from .tclfix import prepare

prepare()
import tkinter as tk
from tkinter import simpledialog, messagebox
from pathlib import Path
from typing import Any, Callable, Optional

from .i18n import t
from .loader import load_world
from .paths import games_dir
from .project import (
    Project,
    copy_for_edit,
    csv_dump,
    csv_load,
    loc_pair,
    loc_value,
    exit_body,
    yaml_dump_text,
    yaml_load_text,
)
from .theme import C, Btn, Entry, Text, font_ui, font_log

KINDS = [
    ("locations", "ed_rooms", "ed_hint_rooms", "ed_new_room", "world"),
    ("items", "ed_items", "ed_hint_items", "ed_new_item", "world"),
    ("npcs", "ed_npcs", "ed_hint_npcs", "ed_new_npc", "world"),
    ("dialogues", "ed_dialogues", "ed_hint_dialogues", "ed_new_talk", "story"),
    ("quests", "ed_quests", "ed_hint_quests", "ed_new_quest", "story"),
    ("encounters", "ed_fights", "ed_hint_fights", "ed_new_fight", "fight"),
    ("abilities", "ed_abilities", "ed_hint_abilities", "ed_new_ability", "fight"),
    ("loot_tables", "ed_loot", "ed_hint_loot", "ed_new_loot", "fight"),
    ("recipes", "ed_recipes", "ed_hint_recipes", "ed_new_recipe", "fight"),
]
KIND_IDS = {row[0] for row in KINDS}
GROUPS = (
    ("world", "ed_nav_world"),
    ("story", "ed_nav_story"),
    ("fight", "ed_nav_fight"),
)
DIRS = ("north", "south", "east", "west", "up", "down")
ITEM_TYPES = ("weapon", "armor", "shield", "accessory", "consumable", "key", "book", "quest", "misc")


class EditorWindow:
    def __init__(self, root: tk.Tk, game_path: Path, lang: str, on_exit: Callable):
        self.root = root
        self.lang = lang
        self.on_exit = on_exit
        src = Path(game_path)
        writable = copy_for_edit(src)
        if writable != src:
            messagebox.showinfo(
                "Quantum RPG",
                t(lang, "ed_copied", path=str(writable)),
            )
        self.project = Project.load(writable)
        self.sel = ("guide", "")
        self.form: Optional[tk.Frame] = None
        self.vars: dict[str, Any] = {}
        root.geometry("1180x760")
        root.minsize(980, 620)
        self.frame = tk.Frame(root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)
        self._build()
        self._fill_tree()
        self._show("guide", "")

    def tr(self, key: str, **kw) -> str:
        return t(self.lang, key, **kw)

    def _build(self) -> None:
        top = tk.Frame(self.frame, bg=C["panel"])
        top.pack(fill="x")
        titles = tk.Frame(top, bg=C["panel"])
        titles.pack(side="left", padx=16, pady=10)
        self.title_lbl = tk.Label(titles, text="", bg=C["panel"], fg=C["fg"], font=font_ui(13, True))
        self.title_lbl.pack(anchor="w")
        self.path_lbl = tk.Label(titles, text="", bg=C["panel"], fg=C["dim"], font=font_ui(8))
        self.path_lbl.pack(anchor="w")

        actions = tk.Frame(top, bg=C["panel"])
        actions.pack(side="right", padx=12, pady=8)
        Btn(actions, text=self.tr("gui_save"), command=self._save, anchor="center", font=font_ui(9, True)).pack(side="left", padx=3)
        Btn(actions, text=self.tr("gui_play"), command=self._play, anchor="center", font=font_ui(9, True)).pack(side="left", padx=3)
        Btn(actions, text=self.tr("ed_validate"), command=self._validate, anchor="center").pack(side="left", padx=3)
        more = tk.Menubutton(
            actions, text=self.tr("ed_more"), bg=C["btn"], fg=C["fg"],
            activebackground=C["btn_hi"], activeforeground=C["fg"],
            relief="flat", bd=0, padx=10, pady=4, font=font_ui(9),
        )
        menu = tk.Menu(more, tearoff=0, bg=C["panel"], fg=C["fg"], activebackground=C["accent"], activeforeground=C["bg"])
        menu.add_command(label=self.tr("ed_play_here"), command=self._play_here)
        menu.add_command(label=self.tr("ed_library"), command=self._library)
        menu.add_command(label=self.tr("ed_package"), command=self._package)
        menu.add_command(label=self.tr("ed_help"), command=self._help)
        more.configure(menu=menu)
        more.pack(side="left", padx=3)
        Btn(actions, text=self.tr("gui_menu"), command=self._leave, anchor="center").pack(side="left", padx=(8, 0))

        body = tk.Frame(self.frame, bg=C["bg"])
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=C["panel"], width=248)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.side = tk.Frame(left, bg=C["panel"])
        self.side.pack(fill="both", expand=True, padx=10, pady=12)

        rule = tk.Frame(body, bg=C["line"], width=1)
        rule.pack(side="left", fill="y")

        right_wrap = tk.Frame(body, bg=C["bg"])
        right_wrap.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(right_wrap, bg=C["bg"], highlightthickness=0, bd=0)
        scroll = tk.Scrollbar(right_wrap, command=self.canvas.yview, width=10)
        self.inner = tk.Frame(self.canvas, bg=C["bg"])
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(1, width=e.width))

        self.status = tk.Label(self.frame, text="", bg=C["panel"], fg=C["dim"], font=font_ui(9), anchor="w")
        self.status.pack(fill="x", ipady=6, padx=16)
        self._set_title()

    def _set_title(self) -> None:
        from .util import loc

        name = loc(self.project.game.get("title") or self.project.path.name, self.lang)
        mark = "  ·  " + self.tr("ed_unsaved_mark") if self.project.dirty else ""
        self.title_lbl.configure(text=f"{name}{mark}")
        self.path_lbl.configure(text=str(self.project.path))

    def _section(self, sel: Optional[tuple] = None) -> str:
        kind, eid = sel or self.sel
        if kind == "index":
            return str(eid)
        return kind

    def _fill_tree(self, keep: Optional[tuple] = None) -> None:
        for child in self.side.winfo_children():
            child.destroy()
        current = self._section(keep)
        self._nav_item("guide", self.tr("ed_nav_start"), current == "guide")
        self._nav_item("game", self.tr("ed_game"), current == "game")
        for group, title_key in GROUPS:
            self._nav_label(self.tr(title_key))
            for kind, label_key, _hint, _new, grp in KINDS:
                if grp != group:
                    continue
                count = len(self.project.table(kind))
                self._nav_item(kind, self.tr(label_key), current == kind, str(count))
        self._nav_label(self.tr("ed_nav_extra"))
        self._nav_item("events", self.tr("ed_events"), current == "events")
        self._nav_item("hooks", self.tr("ed_hooks"), current == "hooks")

    def _nav_label(self, text: str) -> None:
        tk.Label(
            self.side, text=text.upper(), bg=C["panel"], fg=C["dim"],
            font=font_ui(8), anchor="w",
        ).pack(fill="x", pady=(14, 4))

    def _nav_item(self, kind: str, text: str, on: bool, count: str = "") -> None:
        row = tk.Frame(self.side, bg=C["accent"] if on else C["panel"])
        row.pack(fill="x", pady=1)
        inner = tk.Frame(row, bg=C["line"] if on else C["panel"])
        inner.pack(fill="x", padx=(2, 0))
        label = f"{text}    {count}" if count else text
        btn = tk.Button(
            inner, text=label, command=lambda k=kind: self._nav(k),
            bg=C["line"] if on else C["panel"], fg=C["fg"] if on else C["dim"],
            activebackground=C["line"], activeforeground=C["fg"],
            relief="flat", bd=0, anchor="w", padx=10, pady=6,
            font=font_ui(10, on), highlightthickness=0, cursor="hand2",
        )
        btn.pack(fill="x")

    def _nav(self, kind: str) -> None:
        self._flush()
        if kind == "guide":
            self._show("guide", "")
        elif kind in ("game", "events", "hooks"):
            self._show(kind, "")
        else:
            self._show("index", kind)
        self._fill_tree()

    def _kind_row(self, kind: str):
        for row in KINDS:
            if row[0] == kind:
                return row
        return None

    def _add(self, kind: str) -> None:
        eid = simpledialog.askstring("Quantum RPG", self.tr("ed_new_id"), parent=self.root)
        if not eid:
            return
        try:
            self.project.add(kind, eid)
        except ValueError:
            messagebox.showerror("Quantum RPG", self.tr("ed_bad_id"))
            return
        eid = eid.strip().replace(" ", "_")
        self._show(kind, eid)
        self._fill_tree()
        self._set_title()

    def _delete_sel(self) -> None:
        kind, eid = self.sel
        if kind not in KIND_IDS or not eid:
            return
        if not messagebox.askyesno("Quantum RPG", self.tr("ed_delete", id=eid)):
            return
        self.project.delete(kind, eid)
        self._show("index", kind)
        self._fill_tree()
        self._set_title()

    def _flush(self) -> None:
        if self.form is None:
            return
        fn = getattr(self.form, "collect", None)
        if callable(fn):
            token = self.project.freeze()
            try:
                fn()
            except Exception as exc:
                self.status.configure(text=str(exc), fg=C["danger"])
            else:
                if self.project.freeze() != token:
                    self.project.dirty = True
        self._set_title()

    def _clear_form(self) -> None:
        for w in self.inner.winfo_children():
            w.destroy()
        self.form = None
        self.canvas.yview_moveto(0)

    def _page(self, parent, title: str, hint: str) -> None:
        tk.Label(parent, text=title, bg=C["bg"], fg=C["fg"], font=font_ui(18, True), anchor="w").pack(anchor="w")
        if hint:
            tk.Label(
                parent, text=hint, bg=C["bg"], fg=C["dim"], font=font_ui(10),
                wraplength=680, justify="left", anchor="w",
            ).pack(anchor="w", pady=(6, 16))

    def _entity_label(self, kind: str, eid: str) -> str:
        from .util import loc

        row = self.project.table(kind).get(eid) or {}
        if not isinstance(row, dict):
            return eid
        name = loc(row.get("name") or "", self.lang)
        if name and name != eid:
            return f"{name}    {eid}"
        return eid

    def _show(self, kind: str, eid: str) -> None:
        self.sel = (kind, eid)
        self._clear_form()
        box = tk.Frame(self.inner, bg=C["bg"])
        box.pack(fill="both", expand=True, padx=28, pady=22)
        self.form = box
        if kind == "guide":
            self._show_guide(box)
        elif kind == "index":
            self._show_index(box, eid)
        elif kind == "game":
            self._page(box, self.tr("ed_game"), self.tr("ed_hint_game"))
            GameForm(box, self)
        elif kind == "events":
            self._page(box, self.tr("ed_events"), self.tr("ed_hint_events"))
            RawForm(box, self, "events_text", "events.yaml")
        elif kind == "hooks":
            self._page(box, self.tr("ed_hooks"), self.tr("ed_hint_hooks"))
            RawForm(box, self, "hooks_text", "hooks.py")
        else:
            row = self._kind_row(kind)
            title = self._entity_label(kind, eid)
            hint = self.tr(row[2]) if row else ""
            bar = tk.Frame(box, bg=C["bg"])
            bar.pack(fill="x", pady=(0, 8))
            Btn(bar, text="←  " + self.tr("ed_back"), command=lambda k=kind: self._nav(k), anchor="w").pack(side="left")
            Btn(bar, text=self.tr("ed_delete_btn"), command=self._delete_sel, anchor="center").pack(side="right")
            self._page(box, title, hint)
            self._mount(box, kind, eid)
        self.status.configure(text=self.tr("ed_status_ok"), fg=C["dim"])

    def _mount(self, box, kind: str, eid: str) -> None:
        if kind == "locations":
            LocationForm(box, self, eid)
        elif kind == "items":
            ItemForm(box, self, eid)
        elif kind == "npcs":
            NpcForm(box, self, eid)
        elif kind == "dialogues":
            DialogueForm(box, self, eid)
        elif kind == "quests":
            QuestForm(box, self, eid)
        elif kind == "encounters":
            EncounterForm(box, self, eid)
        elif kind == "recipes":
            RecipeForm(box, self, eid)
        elif kind == "abilities":
            AbilityForm(box, self, eid)
        elif kind == "loot_tables":
            LootForm(box, self, eid)

    def _show_guide(self, box) -> None:
        self._page(box, self.tr("ed_guide_title"), self.tr("ed_guide_body"))
        for key in ("ed_guide_1", "ed_guide_2", "ed_guide_3", "ed_guide_4"):
            tk.Label(
                box, text=self.tr(key), bg=C["bg"], fg=C["fg"], font=font_ui(11),
                wraplength=680, justify="left", anchor="w",
            ).pack(anchor="w", pady=3)
        row = tk.Frame(box, bg=C["bg"])
        row.pack(anchor="w", pady=(18, 0))
        Btn(row, text=self.tr("ed_game"), command=lambda: self._nav("game"), anchor="center").pack(side="left")
        Btn(row, text=self.tr("ed_rooms"), command=lambda: self._nav("locations"), anchor="center").pack(side="left", padx=8)
        Btn(row, text=self.tr("gui_play"), command=self._play, anchor="center", font=font_ui(9, True)).pack(side="left")

    def _show_index(self, box, kind: str) -> None:
        row = self._kind_row(kind)
        if not row:
            return
        _kind, label_key, hint_key, new_key, _group = row
        self._page(box, self.tr(label_key), self.tr(hint_key))
        Btn(box, text="+  " + self.tr(new_key), command=lambda k=kind: self._add(k), anchor="w", font=font_ui(10, True)).pack(anchor="w", pady=(0, 12))
        table = self.project.table(kind)
        if not table:
            tk.Label(box, text=self.tr("ed_empty"), bg=C["bg"], fg=C["dim"], font=font_ui(10)).pack(anchor="w")
            return
        for eid in table:
            Btn(
                box, text=self._entity_label(kind, eid),
                command=lambda k=kind, i=eid: self._open_entity(k, i),
                anchor="w",
            ).pack(fill="x", pady=2)

    def _open_entity(self, kind: str, eid: str) -> None:
        self._flush()
        self._show(kind, eid)
        self._fill_tree()

    def _save(self) -> bool:
        self._flush()
        try:
            self.project.save()
        except OSError as exc:
            messagebox.showerror("Quantum RPG", str(exc))
            return False
        self.status.configure(text=self.tr("ed_saved", path=str(self.project.path)), fg=C["ok"])
        self._set_title()
        return True

    def _package(self) -> None:
        if not self._save():
            return
        from .project import package_game

        dest = self.project.path.parent / f"{self.project.path.name}.zip"
        try:
            package_game(self.project.path, dest)
        except OSError as exc:
            messagebox.showerror("Quantum RPG", str(exc))
            return
        self.status.configure(text=self.tr("ed_packaged", path=str(dest)), fg=C["ok"])
        messagebox.showinfo("Quantum RPG", self.tr("ed_packaged", path=str(dest)))

    def _validate(self) -> None:
        if not self._save():
            return
        world = load_world(self.project.path)
        from .check import problems

        found = problems(world)
        lines = [f"ERROR: {e}" for e in world.errors] + [f"WARN: {w}" for w in world.warnings] + found
        if not lines:
            lines = [self.tr("check_ok")]
            self.status.configure(text=lines[0], fg=C["ok"])
        else:
            self.status.configure(text=lines[0], fg=C["danger"])
        messagebox.showinfo("Quantum RPG", "\n".join(lines[:40]))

    def _play(self) -> None:
        if not self._save():
            return
        world = load_world(self.project.path)
        if world.errors:
            messagebox.showerror("Quantum RPG", "\n".join(world.errors))
            return
        from .gui import PlayWindow

        self.frame.pack_forget()

        def back():
            self.frame.pack(fill="both", expand=True)
            self._fill_tree(self.sel)

        PlayWindow(self.root, self.project.path, self.lang, on_exit=back)

    def _play_here(self) -> None:
        kind, eid = self.sel
        if kind != "locations" or not eid:
            messagebox.showinfo("Quantum RPG", self.tr("ed_pick_room"))
            return
        if not self._save():
            return
        world = load_world(self.project.path)
        if world.errors:
            messagebox.showerror("Quantum RPG", "\n".join(world.errors))
            return
        from .gui import PlayWindow

        self.frame.pack_forget()

        def back():
            self.frame.pack(fill="both", expand=True)
            self._fill_tree(self.sel)

        PlayWindow(self.root, self.project.path, self.lang, on_exit=back, start_at=eid)

    def _leave(self) -> None:
        self._flush()
        if self.project.dirty:
            if not messagebox.askyesno("Quantum RPG", self.tr("ed_unsaved")):
                return
        self.frame.destroy()
        self.on_exit()

    def _help(self) -> None:
        from .cheatsheet import HELP

        win = tk.Toplevel(self.root)
        win.title(self.tr("ed_help"))
        win.configure(bg=C["bg"])
        win.geometry("560x520")
        body = Text(win, height=30)
        body.insert("1.0", HELP.get(self.lang) or HELP["en"])
        body.configure(state="disabled")
        body.pack(fill="both", expand=True, padx=8, pady=8)

    def _library(self) -> None:
        from .library import catalog

        bricks = catalog()
        if not bricks:
            messagebox.showinfo("Quantum RPG", self.tr("ed_lib_empty"))
            return
        win = tk.Toplevel(self.root)
        win.title(self.tr("ed_library"))
        win.configure(bg=C["bg"])
        win.geometry("520x480")
        lb = tk.Listbox(
            win, bg=C["panel"], fg=C["fg"], selectbackground=C["accent"],
            selectforeground=C["bg"], relief="flat", font=font_ui(10),
            highlightthickness=0,
        )
        lb.pack(fill="both", expand=True, padx=8, pady=8)
        for b in bricks:
            lb.insert("end", "  " + b.label(self.lang))

        def insert():
            sel = lb.curselection()
            if not sel:
                return
            brick = bricks[sel[0]]
            table = self.project.table(brick.kind) if brick.kind in KIND_IDS or hasattr(self.project, brick.kind) else None
            if table is None:
                if brick.kind == "loot_tables":
                    game = self.project.game
                    tables = dict(game.get("loot_tables") or {})
                    tables[brick.eid] = brick.data.get("drops") or brick.data
                    game["loot_tables"] = tables
                else:
                    return
            else:
                eid = brick.eid
                if eid in table:
                    eid = eid + "_copy"
                    n = 2
                    while eid in table:
                        eid = f"{brick.eid}_{n}"
                        n += 1
                row = dict(brick.data)
                row["id"] = eid
                table[eid] = row
            self.project.dirty = True
            self._fill_tree((brick.kind, brick.eid if brick.kind != "loot_tables" else ""))
            self.status.configure(text=self.tr("ed_imported", id=brick.eid), fg=C["ok"])
            self._set_title()

        Btn(win, text=self.tr("ed_import"), command=insert, anchor="center").pack(pady=8)


# ----- form helpers ----------------------------------------------------------

def _label(parent, text: str) -> None:
    tk.Label(parent, text=text, bg=C["bg"], fg=C["dim"], font=font_ui(8), anchor="w").pack(fill="x", pady=(10, 2))


def _entry(parent, value: str = "", width: int = 48) -> Entry:
    e = Entry(parent, width=width)
    e.insert(0, value)
    e.pack(fill="x")
    return e


def _text(parent, value: str = "", height: int = 4) -> Text:
    w = Text(parent, height=height)
    if value:
        w.insert("1.0", value)
    w.pack(fill="x")
    return w


def _loc(parent, label: str, value, height: int = 0):
    _label(parent, label)
    ru, en = loc_pair(value)
    row = tk.Frame(parent, bg=C["bg"])
    row.pack(fill="x")
    tk.Label(row, text="RU", bg=C["bg"], fg=C["accent"], font=font_ui(8), width=3).pack(side="left")
    if height:
        a = Text(row, height=height, width=40)
        a.insert("1.0", ru)
        a.pack(side="left", fill="x", expand=True)
    else:
        a = Entry(row)
        a.insert(0, ru)
        a.pack(side="left", fill="x", expand=True)
    row2 = tk.Frame(parent, bg=C["bg"])
    row2.pack(fill="x", pady=(2, 0))
    tk.Label(row2, text="EN", bg=C["bg"], fg=C["accent"], font=font_ui(8), width=3).pack(side="left")
    if height:
        b = Text(row2, height=height, width=40)
        b.insert("1.0", en)
        b.pack(side="left", fill="x", expand=True)
    else:
        b = Entry(row2)
        b.insert(0, en)
        b.pack(side="left", fill="x", expand=True)
    return a, b


def _get(w) -> str:
    if isinstance(w, tk.Text):
        return w.get("1.0", "end").rstrip("\n")
    return w.get()


def _check(parent, text: str, value: bool) -> tk.BooleanVar:
    v = tk.BooleanVar(value=bool(value))
    tk.Checkbutton(
        parent, text=text, variable=v, bg=C["bg"], fg=C["fg"],
        selectcolor=C["btn"], activebackground=C["bg"], activeforeground=C["fg"],
        highlightthickness=0, font=font_ui(9),
    ).pack(anchor="w", pady=2)
    return v


def _option(parent, label: str, value: str, choices: tuple[str, ...]) -> tk.StringVar:
    _label(parent, label)
    v = tk.StringVar(value=value if value in choices else (choices[0] if choices else ""))
    tk.OptionMenu(parent, v, *choices).pack(anchor="w")
    return v


# ----- forms -----------------------------------------------------------------

class _Base:
    def __init__(self, parent, editor: EditorWindow):
        self.parent = parent
        self.ed = editor
        parent.collect = self.collect  # type: ignore[attr-defined]

    def collect(self) -> None:
        raise NotImplementedError


class GameForm(_Base):
    def __init__(self, parent, editor):
        super().__init__(parent, editor)
        g = editor.project.game
        player = g.get("player") or {}
        start = g.get("start") or {}
        start_id = start if isinstance(start, str) else (start.get("location") or "")
        win = g.get("win") or {}
        self.id = _labeled(parent, "id", g.get("id") or editor.project.path.name)
        self.title = _loc(parent, "title", g.get("title"))
        self.author = _labeled(parent, "author", g.get("author") or "")
        self.version = _labeled(parent, "version", g.get("version") or "0.1.0")
        self.language = _option(parent, "language", str(g.get("language") or "ru"), ("ru", "en"))
        rooms = tuple(editor.project.locations) or ("start_room",)
        self.start = _option(parent, "start.location", start_id if start_id in rooms else (rooms[0] if rooms else ""), rooms)
        self.intro = _loc(parent, "intro", g.get("intro"), height=4)
        self.pname = _labeled(parent, "player.name", player.get("name") or "")
        self.prompt = _check(parent, "player.name_prompt", player.get("name_prompt"))
        self.hp = _labeled(parent, "player.hp", str(player.get("hp") or 20))
        self.gold = _labeled(parent, "player.gold", str(player.get("gold") or 0))
        stats = player.get("stats") or {}
        self.stats = _labeled(
            parent,
            "player.stats  str,dex,int,con,cha,per",
            ",".join(str(stats.get(k, 10)) for k in ("str", "dex", "int", "con", "cha", "per")),
        )
        self.inv = _labeled(parent, "player.inventory", csv_load(player.get("inventory")))
        rest = tk.Frame(parent, bg=C["bg"])

        def _toggle(box=rest):
            if box.winfo_ismapped():
                box.pack_forget()
            else:
                box.pack(fill="x", pady=(8, 0))

        Btn(parent, text=editor.tr("ed_more_fields"), command=_toggle, anchor="w").pack(anchor="w", pady=(18, 4))
        self.win_flags = _labeled(rest, "win.flags", csv_load(win.get("flags") or win.get("flag")))
        self.win_text = _loc(rest, "win.text", win.get("text"), height=3)
        self.include = _labeled(rest, "include (library files)", csv_load(g.get("include") or g.get("includes")))
        self.class_prompt = _check(rest, "class_prompt", bool(g.get("classes")) if g.get("class_prompt") is None else bool(g.get("class_prompt")))
        self.classes = _yaml_field(rest, "classes (YAML)", yaml_dump_text(g.get("classes")))
        self.factions = _yaml_field(rest, "factions (YAML)", yaml_dump_text(g.get("factions")))
        hunger = g.get("hunger") or {}
        if not isinstance(hunger, dict):
            hunger = {}
        self.hunger_max = _labeled(rest, "hunger.max (empty = off)", str(hunger.get("max") or ""))
        self.hunger_step = _labeled(rest, "hunger.step", str(hunger.get("step") or ""))
        self.audio = _yaml_field(rest, "audio (YAML)", yaml_dump_text(g.get("audio")))
        clock = g.get("time") or {}
        if not isinstance(clock, dict):
            clock = {}
        self.start_hour = _labeled(rest, "time.start_hour", str(clock.get("start_hour") or ""))
        self.rest_hours = _labeled(rest, "time.rest_hours", str(clock.get("rest_hours") or ""))
        self.shop_closed = _labeled(rest, "time.shop_closed  night,evening", csv_load(clock.get("shop_closed")))
        self.night_bonus = _labeled(
            rest, "time.night_encounter_bonus", str(clock.get("night_encounter_bonus") or "")
        )
        self.regions = _yaml_field(rest, "regions (YAML)", yaml_dump_text(g.get("regions")))
        self.roads = _yaml_field(rest, "roads (YAML)", yaml_dump_text(g.get("roads")))
        self.levels = _yaml_field(rest, "levels (YAML)", yaml_dump_text(g.get("levels")))
        self.rumors = _yaml_field(rest, "rumors (YAML)", yaml_dump_text(g.get("rumors")))
        self.scenes = _yaml_field(rest, "scenes (YAML)", yaml_dump_text(g.get("scenes")))
        self.meters = _yaml_field(rest, "meters (YAML)", yaml_dump_text(g.get("meters")))
        self.map = _yaml_field(rest, "map (YAML)", yaml_dump_text(g.get("map")))
        self.ui = _yaml_field(rest, "ui (YAML)", yaml_dump_text(g.get("ui")))
        self.fx = _yaml_field(rest, "fx (YAML)", yaml_dump_text(g.get("fx")))

    def collect(self) -> None:
        g = self.ed.project.game
        g["id"] = _get(self.id)
        g["title"] = loc_value(_get(self.title[0]), _get(self.title[1]))
        g["author"] = _get(self.author)
        g["version"] = _get(self.version)
        g["language"] = self.language.get()
        g["start"] = {"location": self.start.get()}
        g["intro"] = loc_value(_get(self.intro[0]), _get(self.intro[1]))
        flags = csv_dump(_get(self.win_flags))
        g.setdefault("win", {})
        g["win"]["flags"] = flags
        g["win"]["text"] = loc_value(_get(self.win_text[0]), _get(self.win_text[1]))
        p = g.setdefault("player", {})
        if _get(self.pname):
            p["name"] = _get(self.pname)
        p["name_prompt"] = bool(self.prompt.get())
        p["hp"] = int(_get(self.hp) or 20)
        p["max_hp"] = p["hp"]
        p["gold"] = int(_get(self.gold) or 0)
        nums = csv_dump(_get(self.stats))
        keys = ("str", "dex", "int", "con", "cha", "per")
        p["stats"] = {k: int(nums[i]) if i < len(nums) else 10 for i, k in enumerate(keys)}
        p["inventory"] = csv_dump(_get(self.inv))
        inc = csv_dump(_get(self.include))
        if inc:
            g["include"] = inc
        else:
            g.pop("include", None)
        g["class_prompt"] = bool(self.class_prompt.get())
        classes = yaml_load_text(_get(self.classes))
        if classes:
            g["classes"] = classes
        else:
            g.pop("classes", None)
        factions = yaml_load_text(_get(self.factions))
        if factions:
            g["factions"] = factions
        else:
            g.pop("factions", None)
        hunger = dict(g.get("hunger") or {}) if isinstance(g.get("hunger"), dict) else {}
        hmax = _get(self.hunger_max).strip()
        hstep = _get(self.hunger_step).strip()
        if hmax:
            hunger["max"] = int(hmax)
            if hstep:
                hunger["step"] = int(hstep)
            g["hunger"] = hunger
        else:
            g.pop("hunger", None)
        audio = yaml_load_text(_get(self.audio))
        if audio:
            g["audio"] = audio
        else:
            g.pop("audio", None)
        clock = dict(g.get("time") or {}) if isinstance(g.get("time"), dict) else {}
        hour = _get(self.start_hour).strip()
        rest = _get(self.rest_hours).strip()
        closed = csv_dump(_get(self.shop_closed))
        bonus = _get(self.night_bonus).strip()
        if hour:
            clock["start_hour"] = int(hour)
        else:
            clock.pop("start_hour", None)
        if rest:
            clock["rest_hours"] = int(rest)
        else:
            clock.pop("rest_hours", None)
        if closed:
            clock["shop_closed"] = closed
        else:
            clock.pop("shop_closed", None)
        if bonus:
            clock["night_encounter_bonus"] = int(bonus)
        else:
            clock.pop("night_encounter_bonus", None)
        if clock:
            g["time"] = clock
        else:
            g.pop("time", None)
        regions = yaml_load_text(_get(self.regions))
        if regions:
            g["regions"] = regions
        else:
            g.pop("regions", None)
        roads = yaml_load_text(_get(self.roads))
        if roads:
            g["roads"] = roads
        else:
            g.pop("roads", None)
        levels = yaml_load_text(_get(self.levels))
        if levels:
            g["levels"] = levels
        else:
            g.pop("levels", None)
        rumors = yaml_load_text(_get(self.rumors))
        if rumors:
            g["rumors"] = rumors
        else:
            g.pop("rumors", None)
        scenes = yaml_load_text(_get(self.scenes))
        if scenes:
            g["scenes"] = scenes
        else:
            g.pop("scenes", None)
        for key, widget in (
            ("meters", self.meters),
            ("map", self.map),
            ("ui", self.ui),
            ("fx", self.fx),
        ):
            body = yaml_load_text(_get(widget))
            if body:
                g[key] = body
            else:
                g.pop(key, None)


def _labeled(parent, label: str, value: str) -> Entry:
    _label(parent, label)
    return _entry(parent, value)


class LocationForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        loc = editor.project.locations[eid]
        self.name = _loc(parent, "name", loc.get("name"))
        self.desc = _loc(parent, "description", loc.get("description"), height=5)
        self.note_night = _loc(parent, "note_night", loc.get("note_night"), height=2)
        self.dark = _check(parent, "dark", loc.get("dark"))
        self.rest = _check(parent, "rest", loc.get("rest") is not False)
        self.music = _labeled(parent, "music", str(loc.get("music") or ""))
        self.region = _labeled(parent, "region", str(loc.get("region") or ""))
        self.items = _labeled(parent, "items", csv_load(loc.get("items")))
        self.hidden = _labeled(parent, "hidden_items", csv_load(loc.get("hidden_items")))
        self.npcs = _labeled(parent, "npcs", csv_load(loc.get("npcs")))
        search = loc.get("search") or {}
        self.search_dc = _labeled(parent, "search.dc", str(search.get("dc") or ""))
        self.search_reveal = _labeled(parent, "search.reveal", csv_load(search.get("reveal")))
        _label(parent, "exits")
        self.exit_rows = []
        self.exit_box = tk.Frame(parent, bg=C["bg"])
        self.exit_box.pack(fill="x")
        exits = loc.get("exits") or {}
        rooms = tuple(editor.project.locations) or (eid,)
        if not exits:
            self._exit_row("north", "", False, "", False, "", "", "")
        else:
            for d, dest in exits.items():
                if isinstance(dest, dict):
                    trap = dest.get("trap") if isinstance(dest.get("trap"), dict) else {}
                    self._exit_row(
                        d,
                        str(dest.get("to") or ""),
                        bool(dest.get("locked")),
                        str(dest.get("key") or ""),
                        bool(dest.get("hidden")),
                        str(trap.get("dc") or ""),
                        str(trap.get("damage") or ""),
                        str(trap.get("skill") or ""),
                        dest,
                    )
                else:
                    self._exit_row(d, str(dest or ""), False, "", False, "", "", "", dest)
        Btn(parent, text="+ exit", command=lambda: self._exit_row("north", "", False, "", False, "", "", ""), anchor="center").pack(
            pady=6, anchor="w"
        )
        renc = loc.get("random_encounters") or {}
        if not isinstance(renc, dict):
            renc = {}
        self.renc_chance = _labeled(parent, "random.chance", str(renc.get("chance") or ""))
        self.renc_night = _labeled(parent, "random.chance_night", str(renc.get("chance_night") or ""))
        self.renc_once = _check(parent, "random.once", renc.get("once"))
        _label(parent, "random table  encounter, weight")
        self.renc_box = tk.Frame(parent, bg=C["bg"])
        self.renc_box.pack(fill="x")
        self.renc_rows = []
        for row in renc.get("table") or []:
            if isinstance(row, str):
                self._renc_row(row, "1")
            elif isinstance(row, dict):
                self._renc_row(str(row.get("encounter") or ""), str(row.get("weight") or "1"))
        Btn(parent, text="+ encounter", command=lambda: self._renc_row("", "1"), anchor="center").pack(anchor="w", pady=4)
        self.extra = _yaml_field(parent, "extra YAML (on_enter, containers…)", _extra_yaml(loc, KEEP_LOC))

    def _exit_row(self, d, to, locked, key, hidden, trap_dc, trap_damage, trap_skill, original=None):
        row = tk.Frame(self.exit_box, bg=C["bg"])
        row.pack(fill="x", pady=2)
        line = tk.Frame(row, bg=C["bg"])
        line.pack(fill="x")
        dv = tk.StringVar(value=d if d in DIRS else "north")
        tk.OptionMenu(line, dv, *DIRS).pack(side="left")
        to_e = Entry(line, width=16)
        to_e.insert(0, to)
        to_e.pack(side="left", padx=4)
        lv = tk.BooleanVar(value=locked)
        hv = tk.BooleanVar(value=hidden)
        for text, var in (("lock", lv), ("hidden", hv)):
            tk.Checkbutton(
                line, text=text, variable=var, bg=C["bg"], fg=C["fg"], selectcolor=C["btn"],
                activebackground=C["bg"], highlightthickness=0,
            ).pack(side="left")
        key_e = Entry(line, width=12)
        key_e.insert(0, key)
        key_e.pack(side="left", padx=4)
        Btn(line, text="×", command=lambda r=row: self._drop_exit(r), width=2, anchor="center").pack(side="left")
        line2 = tk.Frame(row, bg=C["bg"])
        line2.pack(fill="x", pady=1)
        tk.Label(line2, text="trap dc / damage / skill", bg=C["bg"], fg=C["dim"], font=font_ui(8)).pack(side="left")
        dc_e, dmg_e, skill_e = Entry(line2, width=6), Entry(line2, width=8), Entry(line2, width=8)
        dc_e.insert(0, trap_dc)
        dmg_e.insert(0, trap_damage)
        skill_e.insert(0, trap_skill)
        dc_e.pack(side="left", padx=2)
        dmg_e.pack(side="left", padx=2)
        skill_e.pack(side="left", padx=2)
        self.exit_rows.append((row, dv, to_e, lv, key_e, hv, dc_e, dmg_e, skill_e, original))

    def _renc_row(self, encounter: str, weight: str) -> None:
        row = tk.Frame(self.renc_box, bg=C["bg"])
        row.pack(fill="x", pady=1)
        a, b = Entry(row, width=22), Entry(row, width=6)
        a.insert(0, encounter)
        b.insert(0, weight)
        a.pack(side="left", padx=2)
        b.pack(side="left", padx=2)
        Btn(row, text="×", width=2, anchor="center", command=lambda r=row: self._drop_renc(r)).pack(side="left")
        self.renc_rows.append((row, a, b))

    def _drop_renc(self, row) -> None:
        self.renc_rows = [x for x in self.renc_rows if x[0] is not row]
        row.destroy()

    def _drop_exit(self, row):
        self.exit_rows = [x for x in self.exit_rows if x[0] is not row]
        row.destroy()

    def collect(self) -> None:
        loc = self.ed.project.locations[self.eid]
        loc["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        loc["description"] = loc_value(_get(self.desc[0]), _get(self.desc[1]))
        note = loc_value(_get(self.note_night[0]), _get(self.note_night[1]))
        if note:
            loc["note_night"] = note
        else:
            loc.pop("note_night", None)
        loc["dark"] = bool(self.dark.get())
        loc["rest"] = bool(self.rest.get())
        music = _get(self.music).strip()
        if music:
            loc["music"] = music
        else:
            loc.pop("music", None)
        region = _get(self.region).strip()
        if region:
            loc["region"] = region
        else:
            loc.pop("region", None)
        loc["items"] = csv_dump(_get(self.items))
        loc["hidden_items"] = csv_dump(_get(self.hidden))
        loc["npcs"] = csv_dump(_get(self.npcs))
        dc = _get(self.search_dc).strip()
        reveal = csv_dump(_get(self.search_reveal))
        if dc or reveal:
            search = dict(loc.get("search") or {})
            if dc:
                search["dc"] = int(dc)
            if reveal:
                search["reveal"] = reveal
            loc["search"] = search
        elif "search" in loc and not dc:
            pass
        exits = {}
        for _row, dv, to_e, lv, key_e, hv, dc_e, dmg_e, skill_e, original in self.exit_rows:
            d = dv.get()
            to = to_e.get().strip()
            if not to:
                continue
            exits[d] = exit_body(
                to,
                bool(lv.get()),
                key_e.get().strip(),
                bool(hv.get()),
                dc_e.get(),
                dmg_e.get(),
                skill_e.get(),
                original,
            )
        loc["exits"] = exits
        table = []
        for _r, a, b in self.renc_rows:
            enc = a.get().strip()
            if not enc:
                continue
            weight = b.get().strip()
            table.append({"encounter": enc, "weight": int(weight) if weight.isdigit() else 1})
        chance = _get(self.renc_chance).strip()
        night = _get(self.renc_night).strip()
        if chance or night or table or self.renc_once.get():
            renc = dict(loc.get("random_encounters") or {}) if isinstance(loc.get("random_encounters"), dict) else {}
            if chance:
                renc["chance"] = int(chance)
            else:
                renc.pop("chance", None)
            if night:
                renc["chance_night"] = int(night)
            else:
                renc.pop("chance_night", None)
            renc["once"] = bool(self.renc_once.get())
            if not renc["once"]:
                renc.pop("once", None)
            if table:
                renc["table"] = table
            else:
                renc.pop("table", None)
            loc["random_encounters"] = renc
        else:
            loc.pop("random_encounters", None)
        _merge_extra(loc, _get(self.extra), KEEP_LOC)


KEEP_LOC = {
    "name", "description", "note_night", "dark", "rest", "music", "region", "items", "hidden_items",
    "npcs", "exits", "search", "random_encounters", "id",
}
KEEP_ITEM = {
    "name", "aliases", "description", "type", "slot", "damage", "hit", "ac", "light",
    "heal", "weight", "value", "takeable", "text", "use", "sound", "id",
}
KEEP_NPC = {
    "name", "aliases", "description", "location", "dialogue", "hostile", "encounter",
    "shop", "shop_always", "shop_faction", "shop_discount", "schedule", "wants", "combat", "id",
}


class ItemForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        it = editor.project.items[eid]
        self.name = _loc(parent, "name", it.get("name"))
        self.aliases = _labeled(parent, "aliases", csv_load(it.get("aliases")))
        self.desc = _loc(parent, "description", it.get("description"), height=3)
        self.type = _option(parent, "type", str(it.get("type") or "misc"), ITEM_TYPES)
        self.slot = _labeled(parent, "slot", str(it.get("slot") or ""))
        self.damage = _labeled(parent, "damage", str(it.get("damage") or ""))
        self.hit = _labeled(parent, "hit", str(it.get("hit") or ""))
        self.ac = _labeled(parent, "ac", str(it.get("ac") or ""))
        self.heal = _labeled(parent, "heal", str(it.get("heal") or ""))
        self.value = _labeled(parent, "value", str(it.get("value") or ""))
        self.weight = _labeled(parent, "weight", str(it.get("weight") or ""))
        self.sound = _labeled(parent, "sound", str(it.get("sound") or ""))
        self.light = _check(parent, "light", it.get("light"))
        self.takeable = _check(parent, "takeable", it.get("takeable") is not False)
        use = it.get("use") or {}
        self.use_text = _loc(parent, "use.text", use.get("text") if isinstance(use, dict) else None)
        self.use_consume = _check(parent, "use.consume", bool(isinstance(use, dict) and use.get("consume")))
        self.use_fx = _yaml_field(parent, "use.effects (YAML)", yaml_dump_text(use.get("effects") if isinstance(use, dict) else None))
        self.read = _loc(parent, "text / on_read", it.get("text") or it.get("on_read"), height=4)
        self.extra = _yaml_field(parent, "extra YAML", _extra_yaml(it, KEEP_ITEM))

    def collect(self) -> None:
        it = self.ed.project.items[self.eid]
        it["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        it["aliases"] = csv_dump(_get(self.aliases))
        it["description"] = loc_value(_get(self.desc[0]), _get(self.desc[1]))
        it["type"] = self.type.get()
        for key, w in (
            ("slot", self.slot),
            ("damage", self.damage),
            ("hit", self.hit),
            ("ac", self.ac),
            ("heal", self.heal),
            ("value", self.value),
            ("weight", self.weight),
        ):
            val = _get(w).strip()
            if val == "":
                it.pop(key, None)
            else:
                it[key] = int(val) if val.isdigit() else val
        it["light"] = bool(self.light.get())
        it["takeable"] = bool(self.takeable.get())
        sound = _get(self.sound).strip()
        if sound:
            it["sound"] = sound
        else:
            it.pop("sound", None)
        ut = loc_value(_get(self.use_text[0]), _get(self.use_text[1]))
        fx = yaml_load_text(_get(self.use_fx))
        if ut or fx or self.use_consume.get():
            use = dict(it.get("use") or {}) if isinstance(it.get("use"), dict) else {}
            if ut:
                use["text"] = ut
            use["consume"] = bool(self.use_consume.get())
            if fx:
                use["effects"] = fx
            it["use"] = use
        txt = loc_value(_get(self.read[0]), _get(self.read[1]))
        if txt:
            it["text"] = txt
        _merge_extra(it, _get(self.extra), KEEP_ITEM)


class NpcForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        n = editor.project.npcs[eid]
        rooms = tuple(editor.project.locations) or ("",)
        dlgs = tuple(editor.project.dialogues) or ("",)
        encs = ("",) + tuple(editor.project.encounters)
        self.name = _loc(parent, "name", n.get("name"))
        self.aliases = _labeled(parent, "aliases", csv_load(n.get("aliases")))
        self.desc = _loc(parent, "description", n.get("description"), height=3)
        loc_id = str(n.get("location") or "")
        self.location = _option(parent, "location", loc_id if loc_id in rooms else (rooms[0] if rooms else ""), rooms)
        dlg = str(n.get("dialogue") or eid)
        self.dialogue = _option(parent, "dialogue", dlg if dlg in dlgs else (dlgs[0] if dlgs else ""), dlgs or (eid,))
        enc = str(n.get("encounter") or "")
        self.encounter = _option(parent, "encounter", enc if enc in encs else "", encs)
        self.hostile = _check(parent, "hostile", n.get("hostile"))
        self.shop_always = _check(parent, "shop_always", n.get("shop_always"))
        self.shop_faction = _labeled(parent, "shop_faction", str(n.get("shop_faction") or n.get("price_rep") or ""))
        self.shop_discount = _labeled(parent, "shop_discount %", str(n.get("shop_discount") if n.get("shop_discount") is not None else ""))
        places = ("", "away") + rooms
        sched = n.get("schedule") if isinstance(n.get("schedule"), dict) else {}
        self.sched = {}
        for phase in ("night", "morning", "day", "evening"):
            cur = str(sched.get(phase) or "")
            self.sched[phase] = _option(parent, f"schedule.{phase}", cur if cur in places else "", places)
        combat = n.get("combat") or {}
        if not isinstance(combat, dict):
            combat = {}
        self.combat_hp = _labeled(parent, "combat.hp", str(combat.get("hp") or ""))
        self.combat_attack = _labeled(parent, "combat.attack", str(combat.get("attack") or ""))
        self.cover = _check(parent, "combat.cover (enemies can drop them)", combat.get("cover") is not False)
        self.wants = _labeled(parent, "wants", csv_load(n.get("wants")))
        _label(parent, "shop  item, price, stock")
        self.shop_box = tk.Frame(parent, bg=C["bg"])
        self.shop_box.pack(fill="x")
        self.shop_rows = []
        for row in n.get("shop") or []:
            if isinstance(row, str):
                self._shop_row(row, "", "")
            elif isinstance(row, dict):
                self._shop_row(str(row.get("item") or ""), str(row.get("price") or ""), str(row.get("stock") or ""))
        Btn(parent, text="+ shop item", command=lambda: self._shop_row("", "", ""), anchor="center").pack(anchor="w", pady=4)
        self.extra = _yaml_field(parent, "extra YAML", _extra_yaml(n, KEEP_NPC))

    def _shop_row(self, item, price, stock):
        row = tk.Frame(self.shop_box, bg=C["bg"])
        row.pack(fill="x", pady=1)
        a, b, c = Entry(row, width=18), Entry(row, width=8), Entry(row, width=8)
        a.insert(0, item)
        b.insert(0, price)
        c.insert(0, stock)
        a.pack(side="left", padx=2)
        b.pack(side="left", padx=2)
        c.pack(side="left", padx=2)
        Btn(row, text="×", width=2, anchor="center", command=lambda r=row: self._drop_shop(r)).pack(side="left")
        self.shop_rows.append((row, a, b, c))

    def _drop_shop(self, row):
        self.shop_rows = [x for x in self.shop_rows if x[0] is not row]
        row.destroy()

    def collect(self) -> None:
        n = self.ed.project.npcs[self.eid]
        n["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        n["aliases"] = csv_dump(_get(self.aliases))
        n["description"] = loc_value(_get(self.desc[0]), _get(self.desc[1]))
        n["location"] = self.location.get()
        n["dialogue"] = self.dialogue.get()
        enc = self.encounter.get()
        if enc:
            n["encounter"] = enc
        else:
            n.pop("encounter", None)
        n["hostile"] = bool(self.hostile.get())
        if self.shop_always.get():
            n["shop_always"] = True
        else:
            n.pop("shop_always", None)
        faction = _get(self.shop_faction).strip()
        if faction:
            n["shop_faction"] = faction
        else:
            n.pop("shop_faction", None)
            n.pop("price_rep", None)
        discount = _get(self.shop_discount).strip()
        if discount:
            n["shop_discount"] = int(discount)
        else:
            n.pop("shop_discount", None)
        schedule = {}
        for phase, widget in self.sched.items():
            val = widget.get().strip()
            if val:
                schedule[phase] = val
        if schedule:
            n["schedule"] = schedule
        else:
            n.pop("schedule", None)
        hp = _get(self.combat_hp).strip()
        attack = _get(self.combat_attack).strip()
        if hp or attack or not self.cover.get():
            combat = dict(n.get("combat") or {}) if isinstance(n.get("combat"), dict) else {}
            if hp:
                combat["hp"] = int(hp)
            else:
                combat.pop("hp", None)
            if attack:
                combat["attack"] = attack
            else:
                combat.pop("attack", None)
            if self.cover.get():
                combat.pop("cover", None)
            else:
                combat["cover"] = False
            if combat:
                n["combat"] = combat
            else:
                n.pop("combat", None)
        else:
            n.pop("combat", None)
        n["wants"] = csv_dump(_get(self.wants))
        shop = []
        for _r, a, b, c in self.shop_rows:
            item = a.get().strip()
            if not item:
                continue
            row: dict[str, Any] = {"item": item}
            if b.get().strip():
                row["price"] = int(b.get())
            if c.get().strip():
                row["stock"] = int(c.get())
            shop.append(row)
        if shop:
            n["shop"] = shop
        else:
            n.pop("shop", None)
        _merge_extra(n, _get(self.extra), KEEP_NPC)


class DialogueForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        d = editor.project.dialogues[eid]
        nodes = d.get("nodes") or {}
        self.start = _labeled(parent, "start", str(d.get("start") or "start"))
        _label(parent, "nodes")
        self.node_id = tk.StringVar(value=next(iter(nodes), "start"))
        ids = tuple(nodes) or ("start",)
        self.node_menu = tk.OptionMenu(parent, self.node_id, *ids, command=lambda *_: self._load_node())
        self.node_menu.pack(anchor="w")
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", pady=4)
        Btn(row, text="+ node", command=self._add_node, anchor="center").pack(side="left")
        Btn(row, text="× node", command=self._del_node, anchor="center").pack(side="left", padx=4)
        self.node_box = tk.Frame(parent, bg=C["bg"])
        self.node_box.pack(fill="x")
        self.graph = tk.Canvas(parent, height=160, bg=C["panel"], highlightthickness=0, bd=0)
        self.graph.pack(fill="x", pady=(8, 4))
        self.graph.bind("<Button-1>", self._graph_click)
        self._graph_boxes: dict = {}
        self._widgets: dict[str, Any] = {}
        self._load_node()

    def _nodes(self) -> dict:
        return self.ed.project.dialogues[self.eid].setdefault("nodes", {})

    def _add_node(self) -> None:
        nid = simpledialog.askstring("Quantum RPG", "node id", parent=self.ed.root)
        if not nid:
            return
        self._collect_node()
        self._nodes()[nid] = {"text": {"ru": nid, "en": nid}, "choices": []}
        self.ed.project.dirty = True
        self._reload_menu(nid)

    def _del_node(self) -> None:
        nid = self.node_id.get()
        nodes = self._nodes()
        if nid in nodes and len(nodes) > 1:
            nodes.pop(nid)
            self._reload_menu(next(iter(nodes)))

    def _reload_menu(self, current: str) -> None:
        self._collect_node()
        menu = self.node_menu["menu"]
        menu.delete(0, "end")
        for nid in self._nodes():
            menu.add_command(label=nid, command=lambda n=nid: self._switch(n))
        self.node_id.set(current)
        self._load_node()

    def _switch(self, nid: str) -> None:
        self._collect_node()
        self.node_id.set(nid)
        self._load_node()

    def _load_node(self) -> None:
        for w in self.node_box.winfo_children():
            w.destroy()
        nid = self.node_id.get()
        node = self._nodes().get(nid) or {}
        name = _loc(self.node_box, "text", node.get("text"), height=3)
        end = _check(self.node_box, "end", node.get("end"))
        shop = _check(self.node_box, "shop", node.get("shop"))
        _label(self.node_box, "choices  (text RU / EN / goto / end)")
        box = tk.Frame(self.node_box, bg=C["bg"])
        box.pack(fill="x")
        rows = []

        def add_choice(ch=None):
            ch = ch or {}
            r = tk.Frame(box, bg=C["bg"])
            r.pack(fill="x", pady=4)
            ru, en = loc_pair(ch.get("text"))
            a, b, g = Entry(r), Entry(r), Entry(r, width=14)
            a.insert(0, ru)
            b.insert(0, en)
            g.insert(0, str(ch.get("goto") or ""))
            a.pack(fill="x")
            b.pack(fill="x", pady=1)
            meta = tk.Frame(r, bg=C["bg"])
            meta.pack(fill="x")
            tk.Label(meta, text="goto", bg=C["bg"], fg=C["dim"], font=font_ui(8)).pack(side="left")
            g.pack(side="left", padx=4)
            tk.Label(meta, text="follow", bg=C["bg"], fg=C["dim"], font=font_ui(8)).pack(side="left")
            fol = Entry(meta, width=12)
            fol.insert(0, _choice_follow(ch))
            fol.pack(side="left", padx=4)
            ev = tk.BooleanVar(value=bool(ch.get("end")))
            tk.Checkbutton(
                meta, text="end", variable=ev, bg=C["bg"], fg=C["fg"], selectcolor=C["btn"],
                activebackground=C["bg"], highlightthickness=0,
            ).pack(side="left")
            Btn(meta, text="×", width=2, anchor="center", command=lambda rr=r: drop(rr)).pack(side="left")
            rows.append((r, a, b, g, ev, fol, ch))

        def drop(r):
            nonlocal rows
            rows = [x for x in rows if x[0] is not r]
            r.destroy()

        for ch in node.get("choices") or []:
            add_choice(ch)
        Btn(self.node_box, text="+ choice", command=lambda: add_choice(), anchor="center").pack(anchor="w", pady=4)
        fx = _yaml_field(self.node_box, "node effects YAML", yaml_dump_text(node.get("effects")))
        self._widgets = {"name": name, "end": end, "shop": shop, "rows": rows, "fx": fx, "add": add_choice}
        self._draw_graph()

    def _draw_graph(self) -> None:
        from .graph import dialogue_layout

        if not hasattr(self, "graph"):
            return
        nodes = self._nodes()
        boxes, edges, height = dialogue_layout(nodes)
        self._graph_boxes = boxes
        self.graph.configure(height=max(120, min(height, 280)))
        self.graph.delete("all")
        current = self.node_id.get()
        for src, dst in edges:
            if src not in boxes or dst not in boxes:
                continue
            x1, y1, x2, y2 = boxes[src]
            a1, b1, a2, b2 = boxes[dst]
            self.graph.create_line(
                (x1 + x2) / 2, y2, (a1 + a2) / 2, b1,
                fill=C["dim"], arrow="last",
            )
        for nid, (x1, y1, x2, y2) in boxes.items():
            fill = C["accent"] if nid == current else C["btn"]
            fg = C["bg"] if nid == current else C["fg"]
            self.graph.create_rectangle(x1, y1, x2, y2, fill=fill, outline=C["line"])
            self.graph.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=nid, fill=fg, font=font_ui(8))

    def _graph_click(self, event) -> None:
        for nid, (x1, y1, x2, y2) in self._graph_boxes.items():
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._switch(nid)
                return

    def _collect_node(self) -> None:
        if not self._widgets:
            return
        nid = self.node_id.get()
        node = self._nodes().setdefault(nid, {})
        name = self._widgets["name"]
        node["text"] = loc_value(_get(name[0]), _get(name[1]))
        node["end"] = bool(self._widgets["end"].get())
        if self._widgets["shop"].get():
            node["shop"] = True
        else:
            node.pop("shop", None)
        choices = []
        for _r, a, b, g, ev, fol, original in self._widgets["rows"]:
            text = loc_value(a.get(), b.get())
            if not text:
                continue
            ch = dict(original) if isinstance(original, dict) else {}
            ch["text"] = text
            goto = g.get().strip()
            if goto:
                ch["goto"] = goto
            else:
                ch.pop("goto", None)
            ch["end"] = bool(ev.get())
            if not ch["end"]:
                ch.pop("end", None)
            effects = [
                e for e in (ch.get("effects") or [])
                if not (isinstance(e, dict) and "follow" in e)
            ]
            fid = fol.get().strip()
            if fid:
                effects.append({"follow": fid})
            if effects:
                ch["effects"] = effects
            else:
                ch.pop("effects", None)
            choices.append(ch)
        node["choices"] = choices
        fx = yaml_load_text(_get(self._widgets["fx"]))
        if fx:
            node["effects"] = fx
        elif "effects" in node and not fx:
            node.pop("effects", None)

    def collect(self) -> None:
        self._collect_node()
        self.ed.project.dialogues[self.eid]["start"] = _get(self.start) or "start"


class QuestForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        q = editor.project.quests[eid]
        self.name = _loc(parent, "name", q.get("name"))
        self.desc = _loc(parent, "description", q.get("description"), height=3)
        self.start = _loc(parent, "start_text", q.get("start_text"), height=2)
        self.done = _loc(parent, "done_text", q.get("done_text"), height=2)
        self.auto = _check(parent, "auto_start", q.get("auto_start"))
        self.reward = _yaml_field(parent, "reward (YAML effects)", yaml_dump_text(q.get("reward")))
        _label(parent, "steps  id, ru, en, hours")
        self.step_box = tk.Frame(parent, bg=C["bg"])
        self.step_box.pack(fill="x")
        self.step_rows = []
        for step in q.get("steps") or []:
            if isinstance(step, str):
                self._step_row("", step, "", "")
            elif isinstance(step, dict):
                text = step.get("text") if isinstance(step.get("text"), dict) else {}
                ru = text.get("ru") if isinstance(text, dict) else str(step.get("text") or "")
                en = text.get("en") if isinstance(text, dict) else ""
                self._step_row(str(step.get("id") or ""), str(ru or ""), str(en or ""), str(step.get("within") or ""))
        Btn(parent, text="+ step", command=lambda: self._step_row("", "", "", ""), anchor="center").pack(anchor="w", pady=4)

    def _step_row(self, sid: str, ru: str, en: str, within: str) -> None:
        row = tk.Frame(self.step_box, bg=C["bg"])
        row.pack(fill="x", pady=1)
        a, b, c, d = Entry(row, width=10), Entry(row, width=24), Entry(row, width=24), Entry(row, width=6)
        a.insert(0, sid)
        b.insert(0, ru)
        c.insert(0, en)
        d.insert(0, within)
        a.pack(side="left", padx=2)
        b.pack(side="left", padx=2)
        c.pack(side="left", padx=2)
        d.pack(side="left", padx=2)
        Btn(row, text="×", width=2, anchor="center", command=lambda r=row: self._drop_step(r)).pack(side="left")
        self.step_rows.append((row, a, b, c, d))

    def _drop_step(self, row) -> None:
        self.step_rows = [x for x in self.step_rows if x[0] is not row]
        row.destroy()

    def collect(self) -> None:
        q = self.ed.project.quests[self.eid]
        q["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        q["description"] = loc_value(_get(self.desc[0]), _get(self.desc[1]))
        q["start_text"] = loc_value(_get(self.start[0]), _get(self.start[1]))
        q["done_text"] = loc_value(_get(self.done[0]), _get(self.done[1]))
        q["auto_start"] = bool(self.auto.get())
        rw = yaml_load_text(_get(self.reward))
        if rw:
            q["reward"] = rw
        else:
            q.pop("reward", None)
        steps = []
        old = {
            str(step.get("id")): step
            for step in (q.get("steps") or [])
            if isinstance(step, dict)
        }
        for i, (_row, a, b, c, d) in enumerate(self.step_rows):
            text = loc_value(b.get(), c.get())
            if not text:
                continue
            sid = a.get().strip() or f"s{i + 1}"
            row = {"id": sid, "text": text}
            hours = d.get().strip()
            if hours:
                row["within"] = int(hours)
            prev = old.get(sid) or {}
            if prev.get("on_expire"):
                row["on_expire"] = prev["on_expire"]
            steps.append(row)
        if steps:
            q["steps"] = steps
        else:
            q.pop("steps", None)


class EncounterForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        e = editor.project.encounters[eid]
        self.name = _loc(parent, "name", e.get("name"))
        self.hp = _labeled(parent, "hp", str(e.get("hp") or 8))
        self.attack = _labeled(parent, "attack", str(e.get("attack") or "1d4"))
        self.defense = _labeled(parent, "defense", str(e.get("defense") or 0))
        self.ac = _labeled(parent, "ac", str(e.get("ac") or 10))
        self.xp = _labeled(parent, "xp", str(e.get("xp") or 0))
        self.flee = _labeled(parent, "flee_dc", str(e.get("flee_dc") or ""))
        self.sound = _labeled(parent, "sound", str(e.get("sound") or ""))
        self.music = _labeled(parent, "music", str(e.get("music") or ""))
        self.appear = _loc(parent, "appear", e.get("appear"), height=2)
        self.loot = _labeled(parent, "loot (item ids)", csv_load(_loot_ids(e.get("loot"))))
        self.on_win = _yaml_field(parent, "on_win (YAML)", yaml_dump_text(e.get("on_win")))
        self.on_lose = _yaml_field(parent, "on_lose (YAML)", yaml_dump_text(e.get("on_lose")))

    def collect(self) -> None:
        e = self.ed.project.encounters[self.eid]
        e["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        e["hp"] = int(_get(self.hp) or 8)
        e["attack"] = _get(self.attack) or "1d4"
        e["defense"] = int(_get(self.defense) or 0)
        e["ac"] = int(_get(self.ac) or 10)
        e["xp"] = int(_get(self.xp) or 0)
        flee = _get(self.flee).strip()
        if flee:
            e["flee_dc"] = int(flee)
        else:
            e.pop("flee_dc", None)
        for key, widget in (("sound", self.sound), ("music", self.music)):
            val = _get(widget).strip()
            if val:
                e[key] = val
            else:
                e.pop(key, None)
        e["appear"] = loc_value(_get(self.appear[0]), _get(self.appear[1]))
        loot = csv_dump(_get(self.loot))
        e["loot"] = [{"item": x, "chance": 100} for x in loot]
        w = yaml_load_text(_get(self.on_win))
        if w:
            e["on_win"] = w
        else:
            e.pop("on_win", None)
        lose = yaml_load_text(_get(self.on_lose))
        if lose:
            e["on_lose"] = lose
        else:
            e.pop("on_lose", None)


class RecipeForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        r = editor.project.recipes[eid]
        rooms = ("",) + tuple(self.ed.project.locations)
        self.name = _loc(parent, "name", r.get("name"))
        self.ings = _labeled(parent, "ingredients", csv_load(r.get("ingredients")))
        st = str(r.get("station") or "")
        self.station = _option(parent, "station", st if st in rooms else "", rooms)
        self.result = _labeled(parent, "result", str(r.get("result") or eid))
        self.text = _loc(parent, "text", r.get("text"), height=2)

    def collect(self) -> None:
        r = self.ed.project.recipes[self.eid]
        r["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        r["ingredients"] = csv_dump(_get(self.ings))
        st = self.station.get()
        if st:
            r["station"] = st
        else:
            r.pop("station", None)
        r["result"] = _get(self.result)
        r["text"] = loc_value(_get(self.text[0]), _get(self.text[1]))


class AbilityForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        a = editor.project.abilities[eid]
        classes = tuple((editor.project.game.get("classes") or {})) or ("",)
        current = str(a.get("class") or "")
        if current and current not in classes:
            classes = classes + (current,)
        self.name = _loc(parent, "name", a.get("name"))
        self.klass = _option(parent, "class", current if current in classes else (classes[0] if classes else ""), classes)
        self.mp = _labeled(parent, "mp", str(a.get("mp") or 0))
        self.damage = _labeled(parent, "damage", str(a.get("damage") or "1d6"))
        self.hit = _labeled(parent, "hit", str(a.get("hit") or ""))
        self.text = _loc(parent, "text", a.get("text"), height=2)

    def collect(self) -> None:
        a = self.ed.project.abilities[self.eid]
        a["name"] = loc_value(_get(self.name[0]), _get(self.name[1]))
        klass = self.klass.get().strip()
        if klass:
            a["class"] = klass
        else:
            a.pop("class", None)
        a["mp"] = int(_get(self.mp) or 0)
        a["damage"] = _get(self.damage).strip() or "1d6"
        hit = _get(self.hit).strip()
        if hit:
            a["hit"] = int(hit) if hit.lstrip("-").isdigit() else hit
        else:
            a.pop("hit", None)
        text = loc_value(_get(self.text[0]), _get(self.text[1]))
        if text:
            a["text"] = text
        else:
            a.pop("text", None)


class LootForm(_Base):
    def __init__(self, parent, editor, eid: str):
        super().__init__(parent, editor)
        self.eid = eid
        table = editor.project.loot_tables[eid]
        drops = table.get("drops") if isinstance(table, dict) else table
        _label(parent, "drops  item, chance")
        self.box = tk.Frame(parent, bg=C["bg"])
        self.box.pack(fill="x")
        self.rows = []
        for row in drops or []:
            if isinstance(row, str):
                self._row(row, "100")
            elif isinstance(row, dict):
                self._row(str(row.get("item") or ""), str(row.get("chance") if row.get("chance") is not None else 100))
        if not self.rows:
            self._row("", "100")
        Btn(parent, text="+ drop", command=lambda: self._row("", "100"), anchor="center").pack(anchor="w", pady=4)

    def _row(self, item: str, chance: str) -> None:
        row = tk.Frame(self.box, bg=C["bg"])
        row.pack(fill="x", pady=1)
        a, b = Entry(row, width=22), Entry(row, width=6)
        a.insert(0, item)
        b.insert(0, chance)
        a.pack(side="left", padx=2)
        b.pack(side="left", padx=2)
        Btn(row, text="×", width=2, anchor="center", command=lambda r=row: self._drop(r)).pack(side="left")
        self.rows.append((row, a, b))

    def _drop(self, row) -> None:
        self.rows = [x for x in self.rows if x[0] is not row]
        row.destroy()

    def collect(self) -> None:
        drops = []
        for _r, a, b in self.rows:
            item = a.get().strip()
            if not item:
                continue
            chance = b.get().strip()
            drops.append({"item": item, "chance": int(chance) if chance.isdigit() else 100})
        self.ed.project.loot_tables[self.eid]["drops"] = drops


class RawForm(_Base):
    def __init__(self, parent, editor, attr: str, filename: str):
        super().__init__(parent, editor)
        self.attr = attr
        _label(parent, filename)
        self.body = _text(parent, getattr(editor.project, attr) or "", height=28)

    def collect(self) -> None:
        setattr(self.ed.project, self.attr, _get(self.body))


def _yaml_field(parent, label: str, value: str) -> Text:
    _label(parent, label)
    return _text(parent, value, height=6)


def _extra_yaml(obj: dict, keep: set[str]) -> str:
    extra = {k: v for k, v in obj.items() if k not in keep and not str(k).startswith("_")}
    return yaml_dump_text(extra)


def _merge_extra(obj: dict, text: str, keep: set[str]) -> None:
    extra = yaml_load_text(text)
    # drop previous extra keys that we own via the textarea
    for k in list(obj):
        if k not in keep and not str(k).startswith("_"):
            obj.pop(k, None)
    if isinstance(extra, dict):
        for k, v in extra.items():
            if k not in keep:
                obj[k] = v


def _choice_follow(ch: dict) -> str:
    for eff in ch.get("effects") or []:
        if isinstance(eff, dict) and "follow" in eff:
            val = eff["follow"]
            if isinstance(val, str):
                return val
            if isinstance(val, dict):
                return str(val.get("npc") or val.get("id") or "")
    return ""


def _loot_ids(loot) -> list:
    if not loot:
        return []
    out = []
    for x in loot:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict) and x.get("item"):
            out.append(x["item"])
    return out
