from quantum_rpg.check import problems
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_greyford_holds():
    world = load_world(ROOT / "games" / "greyford")
    assert problems(world) == []
    g = Game(world, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.handle("проверить")
    assert "Всё сходится" in g.ui.text


def test_check_names_the_break():
    world = load_world(ROOT / "games" / "greyford")
    world.locations["square"]["exits"]["west"] = "missing_room"
    world.game["map"]["ford"][0][0] = "no_such_room"
    world.game["fx"]["hooks"]["enter"] = "no_such_fx"
    world.game["rumors"]["ghost"] = {"knows": ["nobody"], "text": { "ru": "..." }}
    world.game["scenes"]["bad"] = {"beats": [{"when": {"meter": {"mana": {"gte": 1}}}}]}
    found = "\n".join(problems(world))
    assert "missing_room" in found
    assert "no_such_room" in found
    assert "no_such_fx" in found
    assert "nobody" in found
    assert "mana" in found
