from quantum_rpg.conditions import check
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford(lines):
    w = load_world(ROOT / "games" / "greyford")
    w.locations["forest"]["random_encounters"] = {"chance": 0, "table": []}
    return Game(w, ui=ScriptedIO(lines), language="ru", seed=1, ask_name=False)


def test_choice_branches_and_plays_once():
    g = _ford(["2"])
    g.handle("сцена thicket")
    assert "чей-то след" in g.ui.text
    assert "saw_track" in g.state.flags
    g.ui.out.clear()
    apply(g, [{"scene": "thicket"}])
    assert "чей-то след" not in g.ui.text
    g.ui.lines.append("2")
    g.handle("сцена thicket")
    assert "чей-то след" in g.ui.text


def test_other_branch_replay_and_ask():
    g = _ford(["1"])
    g.handle("сцена thicket")
    assert "Ветки" in g.ui.text
    assert "saw_track" not in g.state.flags
    g2 = _ford(["мох"])
    g2.world.game["scenes"]["name_it"] = {
        "once": False,
        "beats": [{"ask": {"prompt": "Имя следа?", "var": "track_name", "flag": "named_track"}}],
    }
    apply(g2, [{"scene": "name_it"}])
    assert g2.state.vars["track_name"] == "мох"
    assert check(g2, {"var": {"track_name": "мох"}})
    g3 = _ford([])
    g3.move_to("forest")
    assert "тише" in g3.ui.text
