from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford():
    w = load_world(ROOT / "games" / "greyford")
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_particles_are_symbols_and_sound_is_cued():
    g = _ford()
    heard = []
    g.audio.cue = lambda spec: heard.append(spec)
    apply(g, [{"fx": "sparks"}, {"fx": {"style": "particles", "particles": "rain", "sound": "hit", "text": "дождь"}}])
    assert "*" in g.ui.text
    assert "|" in g.ui.text
    assert "Искры" in g.ui.text
    assert heard == ["hit"]


def test_typewriter_still_prints_the_whole_line():
    g = _ford()
    apply(g, [{"fx": "hill"}])
    assert g.ui.text.count("Ветер на холме") == 1


def test_screens_and_custom_actions():
    g = _ford()
    assert g.screen_show("shop", ["gold"]) == ["gold", "goods", "sell"]
    assert g.ui_actions()[0]["command"] == "look shrine"
    g.world.game["ui"]["screens"]["shop"]["show"] = ["gold"]
    assert g.screen_show("shop", ["gold", "goods", "sell"]) == ["gold"]
    assert g.ui_screens()["shop"]["hint"].startswith("Назови")
