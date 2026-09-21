"""Command-line interface: play, validate, new, list."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .engine import Game, play_path
from .hooks import Hooks
from .loader import load_world
from .ui import ScriptedIO, TerminalIO

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quantum-rpg",
        description="Quantum Text RPG Engine — fully textual, YAML-authored games.",
    )
    parser.add_argument("--version", action="version", version=f"quantum-rpg {__version__}")
    sub = parser.add_subparsers(dest="cmd")

    p_play = sub.add_parser("play", help="Play a game folder")
    p_play.add_argument("game", nargs="?", default="shadow_keep", help="Folder name or path")
    p_play.add_argument("--lang", default=None, choices=["ru", "en"])
    p_play.add_argument("--seed", type=int, default=1)
    p_play.add_argument("--script", help="File with one command per line (for tests)")
    p_play.add_argument("--name", help="Player name (skips prompt)")
    p_play.add_argument("--echo", action="store_true", help="Echo scripted commands")

    p_val = sub.add_parser("validate", help="Check a game folder for errors")
    p_val.add_argument("game", nargs="?", default="shadow_keep")

    p_new = sub.add_parser("new", help="Copy the template into a new game folder")
    p_new.add_argument("name")
    p_new.add_argument("--out", help="Parent directory (default: ./games)")

    sub.add_parser("list", help="List bundled games")

    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        print()
        print("Example:  python -m quantum_rpg play shadow_keep")
        return 0
    if args.cmd == "play":
        return cmd_play(args)
    if args.cmd == "validate":
        return cmd_validate(args)
    if args.cmd == "new":
        return cmd_new(args)
    if args.cmd == "list":
        return cmd_list()
    return 0


def resolve_game(name: str) -> Path:
    p = Path(name)
    if p.exists():
        return p.resolve()
    cand = GAMES / name
    if cand.exists():
        return cand.resolve()
    raise SystemExit(f"Game not found: {name}\nLooked in {p.resolve()} and {cand}")


def cmd_play(args) -> int:
    path = resolve_game(args.game)
    world = load_world(path)
    if world.errors:
        print("Cannot play, fix these errors:")
        for e in world.errors:
            print("  -", e)
        return 1
    lang = args.lang or world.game.get("language") or "ru"
    ui = TerminalIO()
    if args.script:
        lines = Path(args.script).read_text(encoding="utf-8").splitlines()
        lines = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
        ui = ScriptedIO(lines, echo=args.echo)
    game = Game(
        world,
        hooks=Hooks.load(path),
        ui=ui,
        language=lang,
        seed=args.seed,
        ask_name=not bool(args.name),
    )
    if args.name:
        game.state.player.name = args.name
        game.ask_name = False
    game.start()
    return 0 if game.state.ended != "error" else 1


def cmd_validate(args) -> int:
    path = resolve_game(args.game)
    world = load_world(path)
    ok = True
    for e in world.errors:
        print("ERROR:", e)
        ok = False
    for w in world.warnings:
        print("WARN: ", w)
    if ok:
        nloc = len(world.locations)
        nitem = len(world.items)
        nnpc = len(world.npcs)
        print(f"OK  {path.name}: {nloc} locations, {nitem} items, {nnpc} npcs")
        return 0
    return 1


def cmd_new(args) -> int:
    src = GAMES / "template"
    parent = Path(args.out) if args.out else Path.cwd() / "games"
    parent.mkdir(parents=True, exist_ok=True)
    dest = parent / args.name
    if dest.exists():
        print(f"Already exists: {dest}")
        return 1
    shutil.copytree(src, dest)
    print(f"Created {dest}")
    print("Edit the YAML files, then:")
    print(f"  python -m quantum_rpg play {dest}")
    return 0


def cmd_list() -> int:
    if not GAMES.exists():
        print("No bundled games.")
        return 0
    for p in sorted(GAMES.iterdir()):
        if p.is_dir() and (p / "game.yaml").exists():
            print(p.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
