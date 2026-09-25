"""RC.1 regressions. These are bugs, not new features."""

from quantum_rpg.check import problems
from quantum_rpg.combat import run
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.state import GameState
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford(lines=None):
    world = load_world(ROOT / "games" / "greyford")
    return Game(world, ui=ScriptedIO(lines or []), language="ru", seed=1, ask_name=False)


def test_quit_and_a_bad_jump_do_not_spend_the_scene():
    g = _ford()
    g.world.game["scenes"]["ask"] = {
        "once": True,
        "beats": [
            {"say": "первый"},
            {"goto": "missing"},
            {"say": "второй"},
        ],
    }
    apply(g, [{"scene": "ask"}])
    assert "второй" not in g.ui.text
    assert "scene:ask" not in g.state.once
    g2 = _ford(["инвентарь"])
    g2.world.game["scenes"]["ask"] = {
        "once": True,
        "beats": [{"choose": {"prompt": "Да?", "options": [{"label": "Нет"}]}}],
    }
    apply(g2, [{"scene": "ask"}])
    assert "scene:ask" not in g2.state.once
    assert "Инвентарь" in g2.ui.text or "Золото" in g2.ui.text


def test_a_direction_leaves_the_scene_and_is_obeyed():
    g = _ford(["север"])
    g.world.game["scenes"]["ask"] = {
        "once": True,
        "beats": [{"choose": {"prompt": "Да?", "options": [{"label": "Нет", "goto": "no"}]}, "goto": "no"}, {"mark": "no"}, {"say": "нет"}],
    }
    g.state.location = "road"
    apply(g, [{"scene": "ask"}])
    assert g.state.location != "road"
    assert "нет" not in g.ui.text


def test_a_scene_cannot_call_itself_forever():
    g = _ford()
    g.world.game["scenes"]["loop"] = {"once": False, "beats": [{"say": "раз"}, {"scene": "loop"}]}
    apply(g, [{"scene": "loop"}])
    assert g.ui.text.count("раз") == 1


def test_two_phases_and_a_bad_blow_do_not_crash():
    g = _ford(["5", "quit"])
    g.world.encounters["stump"] = {
        "name": {"ru": "Пень", "en": "Stump"},
        "hp": 10,
        "attack": "0",
        "actions": [{"id": "shout", "name": {"ru": "Крикнуть", "en": "Shout"}, "damage": "nope", "say": {"ru": "Эй."}}],
        "phases": [
            {"at_hp": 100, "say": {"ru": "Раз."}},
            {"at_hp": 100, "say": {"ru": "Два."}},
            {"at_hp": "half", "say": {"ru": "Нет."}},
        ],
    }
    assert run(g, "stump") == "abort"
    assert "Раз." in g.ui.text and "Два." in g.ui.text
    assert "Нет." not in g.ui.text
    assert "Эй." in g.ui.text


def test_a_chain_repeats_and_a_scene_effect_still_runs():
    g = _ford()
    g.world.game["fx"]["chain"] = {"repeat": 2, "steps": [{"style": "plain", "text": "пинг"}]}
    apply(g, [{"fx": "chain"}])
    assert g.ui.text.count("пинг") == 2
    g.world.game["scenes"]["line"] = {"once": False, "beats": [{"say": "строка"}]}
    apply(g, [{"scene": "line", "effects": [{"set_flag": "extra"}]}])
    assert "строка" in g.ui.text
    assert "extra" in g.state.flags


def test_save_keeps_an_answer_and_a_nested_scene_is_named():
    g = _ford()
    g.state.vars["track_name"] = "мох"
    g.state.once.add("scene:thicket")
    again = GameState.from_dict(g.state.to_dict())
    assert again.vars["track_name"] == "мох"
    assert "scene:thicket" in again.once
    g.world.game["scenes"]["bad"] = {"beats": [{"scene": "missing_scene"}]}
    assert "missing_scene" in "\n".join(problems(g.world))


def test_a_bad_meter_does_not_stop_a_step():
    g = _ford()
    g.world.game["meters"]["thirst"]["wait"] = "много"
    g.handle("ждать")
    assert g.state.meters["thirst"] == 0
