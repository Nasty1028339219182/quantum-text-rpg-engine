from pathlib import Path

from quantum_rpg.project import exit_body
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]


def test_play_starts_in_the_chosen_room():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False, start_at="inn")
    assert g.state.location == "inn"


def test_exit_form_keeps_trap_and_secret():
    original = {
        "to": "captain",
        "trap": {
            "skill": "dex",
            "dc": 11,
            "damage": "1d4",
            "once": True,
            "text_success": {"ru": "заметил"},
        },
    }
    body = exit_body("captain", False, "", False, "11", "1d4", "dex", original)
    assert body["trap"]["text_success"]["ru"] == "заметил"
    assert "locked" not in body
    assert exit_body("hall", False, "", False, "", "", "", None) == "hall"
    secret = exit_body("cellar", False, "", True, "12", "1d6", "", None)
    assert secret["hidden"] is True
    assert secret["trap"]["dc"] == 12
    assert secret["trap"]["skill"] == "dex"
    assert secret["trap"]["damage"] == "1d6"


def test_validate_names_missing_wav_and_goto(tmp_path: Path):
    (tmp_path / "game.yaml").write_text(
        "title: t\nstart: {location: room}\naudio:\n  music: {theme: audio/nope.wav}\n  sfx: {hit: audio/hit.wav}\n  cues: {take: missing}\n",
        encoding="utf-8",
    )
    (tmp_path / "locations.yaml").write_text(
        "room:\n  name: Room\n  description: x\n  music: theme\n  exits: {north: other}\nother:\n  name: Other\n  description: y\n",
        encoding="utf-8",
    )
    (tmp_path / "dialogues.yaml").write_text(
        "talk:\n  start: start\n  nodes:\n    start:\n      text: hi\n      choices:\n        - text: go\n          goto: nowhere\n",
        encoding="utf-8",
    )
    for name in ("items", "npcs", "quests", "encounters", "recipes"):
        (tmp_path / f"{name}.yaml").write_text("{}\n", encoding="utf-8")
    world = load_world(tmp_path)
    text = "\n".join(world.warnings)
    assert "missing file" in text
    assert "nowhere" in text
    assert not world.errors


def test_shipped_games_have_no_new_author_warnings():
    for name in ("greyford", "shadow_keep", "first_steps"):
        world = load_world(ROOT / "games" / name)
        bad = [w for w in world.warnings if "missing file" in w or "goes to missing" in w or "has no node" in w]
        assert bad == [], bad
