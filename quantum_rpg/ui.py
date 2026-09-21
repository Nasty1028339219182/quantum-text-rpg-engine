"""Minimal terminal IO. No graphics, no colors by default."""

from __future__ import annotations

from typing import Iterable, Optional


class TerminalIO:
    def write(self, text: str) -> None:
        print(text)

    def read(self, prompt: str = "> ") -> str:
        try:
            return input(prompt)
        except EOFError:
            return "quit"


class ScriptedIO:
    """Feed a list of commands. Used by tests and `--script`."""

    def __init__(self, lines: Iterable[str], echo: bool = False):
        self.lines = [str(x) for x in lines]
        self.out: list[str] = []
        self.echo = echo
        self.index = 0

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

    @property
    def text(self) -> str:
        return "\n".join(self.out)
