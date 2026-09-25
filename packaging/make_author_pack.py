"""Build a zip for game authors: source + docs + bat files, no .exe."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from quantum_rpg import __version__

INCLUDE = [
    "LICENSE",
    "README.md",
    "README.ru.md",
    "CHANGELOG.md",
    "КАК_НАЧАТЬ.txt",
    "ИГРАТЬ.bat",
    "launch.py",
    "requirements.txt",
    "pyproject.toml",
    "quantum_rpg",
    "games",
    "library",
    "docs",
    "examples",
    "tests",
    "packaging/play.bat",
    "packaging/play.sh",
    "packaging/validate.bat",
    "packaging/AUTHOR.txt",
    "packaging/quantum-rpg.spec",
]

SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", "saves", "dist", "build"}


def want(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(p in SKIP_PARTS or p.endswith(".pyc") for p in rel.parts):
        return False
    return True


def main() -> None:
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    dest = out_dir / f"quantum-rpg-author-{__version__}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in INCLUDE:
            src = ROOT / item
            if not src.exists():
                continue
            if src.is_file():
                zf.write(src, item.replace("\\", "/"))
                continue
            for p in src.rglob("*"):
                if p.is_file() and want(p):
                    zf.write(p, str(p.relative_to(ROOT)).replace("\\", "/"))
    print(dest)


if __name__ == "__main__":
    main()
