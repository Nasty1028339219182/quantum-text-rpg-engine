from quantum_rpg.engine import Game
from quantum_rpg.gridmap import render, view
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford():
    w = load_world(ROOT / "games" / "greyford")
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_unknown_rooms_stay_boxes_and_a_name_is_a_step():
    g = _ford()
    g.state.visited.add("square")
    text = render(view(g))
    assert "?" in text
    g.handle("карта inn")
    assert g.state.location == "inn"


def test_locked_door_is_a_cross():
    g = _ford()
    wall = _ford()
    wall.world.game["map"] = {"grid": [["square", "forest"]]}
    assert "║" in render(view(wall))
    g.world.locations["mill"]["exits"] = {}
    g.world.locations["square"]["exits"]["east"] = {"to": "mill", "locked": True}
    assert "×" in render(view(g))


def test_other_floor_is_hidden_until_seen_and_notes_stick():
    g = _ford()
    g.handle("карта холм")
    assert "не видел" in g.ui.text
    g.state.visited.add("hill")
    g.ui.out.clear()
    g.handle("карта холм")
    assert "Холм" in g.ui.text
    assert "Площадь" not in g.ui.text.split("Известные места")[-1]
    g.handle("пометка колодец рядом")
    assert g.state.map_notes["square"] == "колодец рядом"
    assert "*" in render(view(g))
