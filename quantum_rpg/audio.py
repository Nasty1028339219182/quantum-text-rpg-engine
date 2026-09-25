"""Optional sound cues. Silent unless a game ships files.

Playback is one WAV voice (winsound on Windows). A richer mixer can
replace `_output` later without touching the game loop.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional


class Audio:
    def __init__(self, root: Path, spec: Any = None):
        self.root = Path(root)
        self.spec = spec if isinstance(spec, dict) else {}
        self._music: Optional[Path] = None

    def cue(self, spec: Any) -> None:
        if not spec or not self.spec:
            return
        if isinstance(spec, str):
            self.play(spec)
            return
        if not isinstance(spec, dict):
            return
        if spec.get("stop"):
            self.stop_music()
        if spec.get("music"):
            self.play_music(str(spec["music"]))
        name = spec.get("sfx") or spec.get("sound")
        if name:
            self.play(str(name))

    def play(self, name: str) -> None:
        path = self._resolve(name, "sfx")
        if path:
            _output(path, loop=False)

    def play_music(self, name: str) -> None:
        path = self._resolve(name, "music")
        if not path or path == self._music:
            return
        self._music = path
        _output(path, loop=True)

    def stop_music(self) -> None:
        self._music = None
        _stop()

    def _resolve(self, name: str, kind: str) -> Optional[Path]:
        table = self.spec.get(kind) or self.spec.get("sounds") or {}
        rel = table.get(name, name) if isinstance(table, dict) else name
        path = Path(str(rel))
        if not path.is_absolute():
            path = self.root / path
        if path.is_file():
            return path
        return None


def _output(path: Path, loop: bool) -> None:
    if sys.platform != "win32" or path.suffix.lower() != ".wav":
        return
    try:
        import winsound

        flags = winsound.SND_FILENAME | winsound.SND_ASYNC
        if loop:
            flags |= winsound.SND_LOOP
        winsound.PlaySound(str(path), flags)
    except Exception:
        return


def _stop() -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound

        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        return
