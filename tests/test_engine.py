from pathlib import Path

from quantum_rpg.engine import Game
from quantum_rpg.hooks import Hooks
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "games" / "shadow_keep"
TEMPLATE = ROOT / "games" / "template"


def make_game(script, lang="ru", seed=1, path=DEMO):
    world = load_world(path)
    ui = ScriptedIO(script)
    game = Game(world, hooks=Hooks.load(path), ui=ui, language=lang, seed=seed, ask_name=False)
    game.start()
    return game, ui


def test_demo_validates():
    world = load_world(DEMO)
    assert world.errors == []
    assert "courtyard" in world.locations
    assert world.start_location == "courtyard"


def test_template_validates():
    world = load_world(TEMPLATE)
    assert world.errors == []


def test_look_and_inventory():
    game, ui = make_game(["осмотреться", "инвентарь", "характеристики", "помощь", "выход"])
    text = ui.text.lower()
    assert "двор" in text or "courtyard" in text
    assert "факел" in text
    assert "помощь" in text or "команды" in text or "осмотреться" in text


def test_take_and_move():
    game, ui = make_game(
        [
            "восток",
            "искать",
            "взять ключ",
            "взять вилы",
            "инвентарь",
            "запад",
            "выход",
        ]
    )
    assert game.has_item("iron_key")
    assert game.has_item("pitchfork")
    assert game.state.location == "courtyard"


def test_language_switch():
    game, ui = make_game(["язык en", "look", "quit"], lang="ru")
    assert game.lang == "en"
    assert "Courtyard" in ui.text or "courtyard" in ui.text.lower()


def test_save_load(tmp_path, monkeypatch):
    game, _ = make_game(["восток", "сохранить testdemo", "выход"])
    assert game.state.location == "stables"
    game2, ui = make_game(["загрузить testdemo", "выход"])
    assert game2.state.location == "stables"


def test_template_short_win():
    game, ui = make_game(["север", "выход"], path=TEMPLATE)
    assert "game_won" in game.state.flags or game.state.ended == "win"
