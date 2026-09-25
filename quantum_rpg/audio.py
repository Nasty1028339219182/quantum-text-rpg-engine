"""WAV music and effects mixed together.

Two levels: music_volume and sfx_volume, 0–100. On Windows the mix
goes out through one stream, so a coin does not cut the loop. Missing
files stay silent. Tests never open the device.
"""

from __future__ import annotations

import struct
import sys
import threading
import time
import wave
from pathlib import Path
from typing import Any, Optional

RATE = 22050
FRAMES = 1024


def clamp_volume(value: Any, default: int = 100) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(100, n))


class Audio:
    def __init__(self, root: Path, spec: Any = None):
        self.root = Path(root)
        self.spec = spec if isinstance(spec, dict) else {}
        self.muted = False
        self.music_volume = clamp_volume(self.spec.get("music_volume", 80), 80)
        self.sfx_volume = clamp_volume(self.spec.get("sfx_volume", 100), 100)
        self._lock = threading.Lock()
        self._cache: dict[str, list[int]] = {}
        self._music_path: Optional[str] = None
        self._music_samples: Optional[list[int]] = None
        self._music_pos = 0
        self._sfx: list[dict] = []
        self._dead = False
        self._thread: Optional[threading.Thread] = None

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
        if not self._on() or self.sfx_volume <= 0:
            return
        samples = self._samples(name, "sfx")
        if not samples:
            return
        with self._lock:
            self._sfx.append({"samples": samples, "pos": 0})
        self._ensure_device()

    def play_music(self, name: str, force: bool = False) -> None:
        if not self._on():
            return
        path = self._resolve(name, "music")
        if not path:
            return
        key = str(path)
        if key == self._music_path and not force:
            return
        samples = self._samples(name, "music")
        if not samples:
            return
        with self._lock:
            self._music_path = key
            self._music_samples = samples
            self._music_pos = 0
        self._ensure_device()

    def stop_music(self) -> None:
        with self._lock:
            self._music_path = None
            self._music_samples = None
            self._music_pos = 0
            self._sfx.clear()

    def shutdown(self) -> None:
        self._dead = True
        self.stop_music()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=0.5)

    def render(self, frames: int) -> list[int]:
        """Mix the next chunk. Music keeps its place while effects play."""
        out = [0] * frames
        music_gain = (self.music_volume / 100) if self._on() else 0
        sfx_gain = (self.sfx_volume / 100) if self._on() else 0
        samples = self._music_samples
        if samples and music_gain:
            count = len(samples)
            pos = self._music_pos
            for i in range(frames):
                out[i] += int(samples[pos] * music_gain)
                pos += 1
                if pos >= count:
                    pos = 0
            self._music_pos = pos
        elif samples:
            self._music_pos = (self._music_pos + frames) % len(samples)
        alive = []
        for item in self._sfx:
            data = item["samples"]
            pos = item["pos"]
            for i in range(frames):
                if pos >= len(data):
                    break
                out[i] += int(data[pos] * sfx_gain)
                pos += 1
            if pos < len(data):
                item["pos"] = pos
                alive.append(item)
        self._sfx = alive
        for i, value in enumerate(out):
            if value > 32767:
                out[i] = 32767
            elif value < -32768:
                out[i] = -32768
        return out

    def _on(self) -> bool:
        return not self.muted and self.spec.get("enabled") is not False

    def _samples(self, name: str, kind: str) -> list[int]:
        path = self._resolve(name, kind)
        if not path:
            return []
        key = str(path)
        if key not in self._cache:
            self._cache[key] = _load_wav(path)
        return self._cache[key]

    def _resolve(self, name: str, kind: str) -> Optional[Path]:
        table = self.spec.get(kind) or {}
        rel = table.get(name, name) if isinstance(table, dict) else name
        path = Path(str(rel))
        if not path.is_absolute():
            path = self.root / path
        if path.is_file() and path.suffix.lower() == ".wav":
            return path
        return None

    def _ensure_device(self) -> None:
        if self._thread or self._dead:
            return
        if sys.platform != "win32" or "pytest" in sys.modules:
            return
        self._thread = threading.Thread(target=self._loop, name="quantum-audio", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        device = _WaveOut()
        if not device.ok:
            return
        try:
            while not self._dead:
                with self._lock:
                    busy = self._music_samples is not None or bool(self._sfx)
                    chunk = self.render(FRAMES) if busy else None
                if chunk is None:
                    time.sleep(0.04)
                    continue
                device.write(struct.pack("<" + "h" * len(chunk), *chunk))
        finally:
            device.close()


def _load_wav(path: Path) -> list[int]:
    try:
        with wave.open(str(path)) as handle:
            channels = handle.getnchannels()
            width = handle.getsampwidth()
            rate = handle.getframerate() or RATE
            raw = handle.readframes(handle.getnframes())
    except Exception:
        return []
    if width == 2:
        count = len(raw) // 2
        values = list(struct.unpack("<" + "h" * count, raw))
    elif width == 1:
        values = [((byte - 128) << 8) for byte in raw]
    else:
        return []
    if channels > 1:
        mixed = []
        for index in range(0, len(values) - channels + 1, channels):
            mixed.append(sum(values[index:index + channels]) // channels)
        values = mixed
    if rate != RATE and values:
        stretched: list[int] = []
        step = rate / RATE
        pos = 0.0
        last = len(values) - 1
        while int(pos) <= last:
            stretched.append(values[int(pos)])
            pos += step
        values = stretched
    return values


class _WaveOut:
    def __init__(self) -> None:
        self.ok = False
        self.slots: list[tuple[Any, Any]] = []
        self.winmm = None
        self.handle = None
        try:
            import ctypes

            self.ctypes = ctypes
            self.winmm = ctypes.WinDLL("winmm")
            self.handle = ctypes.c_void_p()
            fmt = _WAVEFORMATEX(1, 1, RATE, RATE * 2, 2, 16, 0)
            rc = self.winmm.waveOutOpen(
                ctypes.byref(self.handle),
                ctypes.c_uint(0xFFFFFFFF),
                ctypes.byref(fmt),
                0,
                0,
                0,
            )
            self.ok = rc == 0
            self._fmt_size = ctypes.sizeof(_WAVEHDR)
        except Exception:
            self.ok = False

    def write(self, pcm: bytes) -> None:
        if not self.ok or not pcm:
            return
        self._reap()
        guard = 0
        while len(self.slots) >= 4 and guard < 50:
            time.sleep(0.01)
            self._reap()
            guard += 1
        buf = self.ctypes.create_string_buffer(pcm)
        hdr = _WAVEHDR()
        hdr.lpData = self.ctypes.cast(buf, self.ctypes.c_void_p)
        hdr.dwBufferLength = len(pcm)
        self.winmm.waveOutPrepareHeader(self.handle, self.ctypes.byref(hdr), self._fmt_size)
        self.winmm.waveOutWrite(self.handle, self.ctypes.byref(hdr), self._fmt_size)
        self.slots.append((hdr, buf))

    def _reap(self) -> None:
        stay = []
        for hdr, buf in self.slots:
            if hdr.dwFlags & 1:
                self.winmm.waveOutUnprepareHeader(self.handle, self.ctypes.byref(hdr), self._fmt_size)
            else:
                stay.append((hdr, buf))
        self.slots = stay

    def close(self) -> None:
        if not self.ok:
            return
        try:
            self.winmm.waveOutReset(self.handle)
            self._reap()
            self.winmm.waveOutClose(self.handle)
        except Exception:
            return
        self.ok = False


class _WAVEFORMATEX(struct.Structure if False else object):
    pass


# ctypes structures are created lazily so import stays free of ctypes on purpose.
def _bind_structures() -> None:
    import ctypes

    class WAVEFORMATEX(ctypes.Structure):
        _fields_ = [
            ("wFormatTag", ctypes.c_ushort),
            ("nChannels", ctypes.c_ushort),
            ("nSamplesPerSec", ctypes.c_uint),
            ("nAvgBytesPerSec", ctypes.c_uint),
            ("nBlockAlign", ctypes.c_ushort),
            ("wBitsPerSample", ctypes.c_ushort),
            ("cbSize", ctypes.c_ushort),
        ]

    class WAVEHDR(ctypes.Structure):
        _fields_ = [
            ("lpData", ctypes.c_void_p),
            ("dwBufferLength", ctypes.c_uint),
            ("dwBytesRecorded", ctypes.c_uint),
            ("dwUser", ctypes.c_void_p),
            ("dwFlags", ctypes.c_uint),
            ("dwLoops", ctypes.c_uint),
            ("lpNext", ctypes.c_void_p),
            ("reserved", ctypes.c_void_p),
        ]

    global _WAVEFORMATEX, _WAVEHDR
    _WAVEFORMATEX = WAVEFORMATEX
    _WAVEHDR = WAVEHDR


_bind_structures()
