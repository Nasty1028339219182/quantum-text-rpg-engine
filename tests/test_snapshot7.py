from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford():
    w = load_world(ROOT / "games" / "greyford")
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_chain_repeat_quote_and_when():
    g = _ford()
    apply(g, [{"fx": {"steps": ["sparks", {"style": "quote", "text": "тише"}], "repeat": 1}}])
    assert "Искры" in g.ui.text
    assert "« тише »" in g.ui.text
    g.ui.out.clear()
    apply(g, [{"fx": {"style": "plain", "text": "раз", "repeat": 2}}])
    assert g.ui.text.count("раз") == 2
    g.ui.out.clear()
    apply(g, [{"fx": {"style": "plain", "text": "нет", "when": {"flag": "nope"}}}])
    assert "нет" not in g.ui.text


def test_enter_and_quest_hooks():
    g = _ford()
    g.world.locations["forest"]["random_encounters"] = {"chance": 0, "table": []}
    g.move_to("forest")
    assert "тише" in g.ui.text
    apply(g, [{"start_quest": "missing_mira"}, {"complete_quest": "missing_mira"}])
    assert "КОНЕЦ СЛЕДА" in g.ui.text
    assert "Искры" in g.ui.text
