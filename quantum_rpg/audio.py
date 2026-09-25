"""WAV music and sound effects. Silent when a file is missing.

Music loops. A sound effect borrows the one Windows voice, then the
music starts again. Other systems do nothing, so tests stay quiet.
"""

from __future__ import annotations

import sys
import threading
import wave
from pathlib import Path
from typing import Any, Optional


class Audio:
    def __init__(self, root: Path, spec: Any = None):
        self.root = Path(root)
        self.spec = spec if isinstance(spec, dict) else {}
        self.muted = False
        self._music: Optional[Path] = None
        self._timer: Optional[threading.Timer] = None

    def event(self, name: str) -> None:
        table = self.spec.get("cues") or self.spec.get("on") or self.spec.get(True) or {}
        if isinstance(table, dict) and name in table:
            self.cue(table.get(name))

    def cue(self, spec: Any) -> None:
        if not spec or not self._on():
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
        if not self._on():
            return
        path = self._resolve(name, "sfx")
        if not path:
            return
        _output(path, loop=False)
        self._resume_after(path)

    def play_music(self, name: str, force: bool = False) -> None:
        if not self._on():
            return
        path = self._resolve(name, "music")
        if not path:
            return
        if path == self._music and not force:
            return
        self._music = path
        self._cancel()
        _output(path, loop=True)

    def stop_music(self) -> None:
        self._music = None
        self._cancel()
        _stop()

    def _on(self) -> bool:
        if self.muted or self.spec.get("enabled") is False:
            return False
        return True

    def _resume_after(self, sfx: Path) -> None:
        music = self._music
        if not music:
            return
        self._cancel()
        delay = _seconds(sfx) + 0.05

        def resume() -> None:
            if self._music == music and self._on():
                _output(music, loop=True)

        self._timer = threading.Timer(delay, resume)
        self._timer.daemon = True
        self._timer.start()

    def _cancel(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _resolve(self, name: str, kind: str) -> Optional[Path]:
        table = self.spec.get(kind) or {}
        rel = table.get(name, name) if isinstance(table, dict) else name
        path = Path(str(rel))
        if not path.is_absolute():
            path = self.root / path
        if path.is_file() and path.suffix.lower() == ".wav":
            return path
        return None


def _seconds(path: Path) -> float:
    try:
        with wave.open(str(path)) as handle:
            rate = handle.getframerate() or 1
            return max(0.05, handle.getnframes() / float(rate))
    except Exception:
        return 0.4


def _output(path: Path, loop: bool) -> None:
    if sys.platform != "win32" or "pytest" in sys.modules:
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
    if sys.platform != "win32" or "pytest" in sys.modules:
        return
    try:
        import winsound

        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        return
