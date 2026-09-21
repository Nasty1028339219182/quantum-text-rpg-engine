from pathlib import Path

from quantum_rpg.engine import Game
from quantum_rpg.hooks import Hooks
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "games" / "shadow_keep"
SCRIPT = Path(__file__).with_name("walkthrough.txt")


def test_shadow_keep_true_ending():
    lines = [
        ln.strip()
        for ln in SCRIPT.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    world = load_world(DEMO)
    assert not world.errors
    ui = ScriptedIO(lines)
    game = Game(world, hooks=Hooks.load(DEMO), ui=ui, language="ru", seed=7, ask_name=False)
    game.state.player.name = "Тестер"
    ending = game.start()
    assert "demon_slain" in game.state.flags or ending == "win"
    assert ending == "win"
    assert "ПОБЕДА" in ui.text or "Тень снята" in ui.text
