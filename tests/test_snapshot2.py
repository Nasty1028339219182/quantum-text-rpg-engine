import zipfile
from pathlib import Path

from quantum_rpg.abilities import available
from quantum_rpg.dialogue import run as run_dialogue
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.project import package_game
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
FORD = ROOT / "games" / "greyford"


def _game():
    w = load_world(FORD)
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_step_expires_after_its_hours():
    g = _game()
    apply(g, [{"start_quest": "missing_mira"}])
    apply(g, [{"advance_quest": {"quest": "missing_mira", "step": "home"}}])
    assert g.state.quest_deadlines["missing_mira"]["at"] == 36
    g.state.time = 36
    g._check_deadlines()
    assert g.state.quests["missing_mira"] == "failed"
    assert "missing_mira" not in g.state.quest_deadlines


def test_level_choice_replaces_free_hp():
    g = _game()
    g.world.game["levels"] = [
        {"text": {"ru": "Сила", "en": "Strength"}, "effects": [{"modify_stat": {"str": 1}}]},
        {"text": {"ru": "Язык", "en": "Tongue"}, "effects": [{"modify_stat": {"cha": 2}}]},
    ]
    g.ui = ScriptedIO(["2"])
    before = g.state.player.max_hp
    cha = g.state.player.stats["cha"]
    g.add_xp(40)
    assert g.state.player.level == 2
    assert g.state.player.max_hp == before
    assert g.state.player.stats["cha"] == cha + 2
    assert g.state.player.stats["str"] == 12


def test_no_levels_still_grants_hp():
    g = _game()
    before = g.state.player.max_hp
    g.add_xp(40)
    assert g.state.player.level == 2
    assert g.state.player.max_hp == before + 4


def test_give_ability_unlocks_it():
    g = _game()
    g.world.abilities["shove"] = {"name": "shove", "class": "warrior"}
    assert available(g) == []
    apply(g, [{"give_ability": "shove"}])
    assert available(g)[0][0] == "shove"


def test_rumor_is_said_once():
    g = _game()
    g.state.flags.add("asked_hilda")
    g.ui = ScriptedIO(["1", "1"])
    run_dialogue(g, "osip")
    assert "mira_south" in g.state.heard_rumors
    assert "Хильда права" in g.ui.text
    g.ui = ScriptedIO(["1"])
    run_dialogue(g, "osip")
    assert "Хильда права" not in g.ui.text


def test_package_contains_one_game_and_its_includes(tmp_path: Path):
    dest = tmp_path / "greyford.zip"
    package_game(FORD, dest)
    names = zipfile.ZipFile(dest).namelist()
    assert "greyford/game.yaml" in names
    assert "greyford/items/weapons.yaml" in names
    assert not any("shadow_keep" in name for name in names)
    assert not any(name.startswith("greyford/saves/") for name in names)
