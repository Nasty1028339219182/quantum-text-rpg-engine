from pathlib import Path

from quantum_rpg.conditions import check
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
FORD = ROOT / "games" / "greyford"


def test_steps_advance_then_complete():
    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    apply(g, [{"start_quest": "missing_mira"}])
    assert g.state.quests["missing_mira"] == "active"
    assert g.state.quest_steps["missing_mira"] == 0
    assert check(g, {"quest_step": {"missing_mira": "ask"}})
    assert any("Спросить" in line for line in g.state.journal)
    apply(g, [{"advance_quest": "missing_mira"}])
    assert g.state.quest_steps["missing_mira"] == 1
    apply(g, [{"advance_quest": {"quest": "missing_mira", "step": "ask"}}])
    assert g.state.quest_steps["missing_mira"] == 1
    apply(g, [{"advance_quest": "missing_mira"}])
    apply(g, [{"advance_quest": "missing_mira"}])
    assert g.state.quests["missing_mira"] == "done"
    assert g.state.player.xp == 20
    apply(g, [{"advance_quest": "missing_mira"}])
    assert g.state.player.xp == 20


def test_quest_without_steps_is_unchanged():
    w = load_world(ROOT / "games" / "shadow_keep")
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    apply(g, [{"start_quest": "investigate"}])
    apply(g, [{"advance_quest": "investigate"}])
    assert g.state.quests["investigate"] == "active"
    assert "investigate" not in g.state.quest_steps
