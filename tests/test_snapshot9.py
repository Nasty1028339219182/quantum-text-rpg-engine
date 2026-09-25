from quantum_rpg.combat import run
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _game(lines):
    w = load_world(ROOT / "games" / "greyford")
    w.encounters["stump"] = {
        "name": {"ru": "Пень", "en": "Stump"},
        "hp": 10,
        "attack": "0",
        "actions": [
            {
                "id": "shout",
                "name": {"ru": "Крикнуть", "en": "Shout"},
                "when": {"flag": "can_shout"},
                "damage": 6,
                "say": {"ru": "Эй.", "en": "Hey."},
                "effects": [{"set_flag": "shouted"}],
            }
        ],
        "phases": [
            {"id": "low", "at_hp": 50, "say": {"ru": "Пень трещит.", "en": "The stump cracks."}}
        ],
    }
    return Game(w, ui=ScriptedIO(lines), language="ru", seed=1, ask_name=False)


def test_author_action_hurts_and_phase_speaks_once():
    g = _game(["5", "quit"])
    g.state.flags.add("can_shout")
    assert run(g, "stump") == "abort"
    assert "Эй." in g.ui.text
    assert "Пень трещит." in g.ui.text
    assert "shouted" in g.state.flags
    assert g.ui.text.count("Пень трещит.") == 1


def test_hidden_action_is_not_a_button():
    g = _game(["5", "quit"])
    run(g, "stump")
    assert "Крикнуть" not in g.ui.text
    assert "Эй." not in g.ui.text
