"""IO backends: terminal, scripted tests, thread-safe queue for the window UI."""

from __future__ import annotations

import queue
from typing import Any, Iterable


class TerminalIO:
    def write(self, text: str) -> None:
        print(text)

    def read(self, prompt: str = "> ") -> str:
        try:
            return input(prompt)
        except EOFError:
            return "quit"

    def set_choices(self, choices: list) -> None:
        return None


class ScriptedIO:
    """Feed a list of commands. Used by tests and `--script`."""

    def __init__(self, lines: Iterable[str], echo: bool = False):
        self.lines = [str(x) for x in lines]
        self.out: list[str] = []
        self.echo = echo
        self.index = 0
        self.choices: list = []

    def write(self, text: str) -> None:
        self.out.append(text if text is not None else "")
        if self.echo:
            print(text)

    def read(self, prompt: str = "> ") -> str:
        if self.index >= len(self.lines):
            return "quit"
        line = self.lines[self.index]
        self.index += 1
        if self.echo:
            print(f"{prompt}{line}")
        return line

    def set_choices(self, choices: list) -> None:
        self.choices = list(choices or [])

    @property
    def text(self) -> str:
        return "\n".join(self.out)


class QueueIO:
    """Game thread writes here; the Tk window reads and submits commands."""

    def __init__(self):
        self.out: queue.Queue = queue.Queue()
        self.inp: queue.Queue = queue.Queue()
        self.game = None
        self.choices: list = []

    def _snap(self) -> dict | None:
        g = self.game
        if g is None:
            return None
        try:
            return g.snapshot()
        except Exception:
            return None

    def write(self, text: str) -> None:
        self.out.put({"op": "write", "text": text, "snap": self._snap()})

    def read(self, prompt: str = "> ") -> str:
        self.out.put({"op": "read", "prompt": prompt, "snap": self._snap(), "choices": list(self.choices)})
        line = self.inp.get()
        return "" if line is None else str(line)

    def set_choices(self, choices: list) -> None:
        self.choices = list(choices or [])
        self.out.put({"op": "choices", "choices": self.choices, "snap": self._snap()})

    def submit(self, line: str) -> None:
        self.inp.put(line)

    def close(self) -> None:
        try:
            self.inp.put_nowait("quit")
        except Exception:
            pass
        self.out.put({"op": "ended", "text": "", "snap": self._snap()})
