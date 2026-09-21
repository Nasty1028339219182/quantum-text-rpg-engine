"""Optional Python hooks. A game folder may contain hooks.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Optional


class Hooks:
    def __init__(self, module: Optional[ModuleType] = None):
        self.module = module

    @classmethod
    def load(cls, game_dir: Path) -> "Hooks":
        path = Path(game_dir) / "hooks.py"
        if not path.exists():
            return cls(None)
        spec = importlib.util.spec_from_file_location("qtrpg_game_hooks", path)
        if spec is None or spec.loader is None:
            return cls(None)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["qtrpg_game_hooks"] = mod
        spec.loader.exec_module(mod)
        return cls(mod)

    def call(self, name: str, *args, **kwargs) -> Any:
        if self.module is None:
            return None
        fn = getattr(self.module, name, None)
        if not callable(fn):
            return None
        return fn(*args, **kwargs)

    def has(self, name: str) -> bool:
        return self.module is not None and callable(getattr(self.module, name, None))
