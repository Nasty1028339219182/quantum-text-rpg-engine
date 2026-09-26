# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "launch.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "games" / "shadow_keep"), "games/shadow_keep"),
        (str(root / "games" / "template"), "games/template"),
        (str(root / "games" / "greyford"), "games/greyford"),
        (str(root / "games" / "first_steps"), "games/first_steps"),
        (str(root / "library"), "library"),
    ],
    hiddenimports=[
        "yaml",
        "quantum_rpg.gui",
        "quantum_rpg.editor",
        "quantum_rpg.engine",
        "quantum_rpg.project",
        "quantum_rpg.theme",
        "quantum_rpg.library",
        "quantum_rpg.loot",
        "quantum_rpg.cheatsheet",
        "quantum_rpg.clock",
        "quantum_rpg.abilities",
        "quantum_rpg.graph",
        "quantum_rpg.audio",
        "quantum_rpg.scenes",
        "quantum_rpg.check",
        "quantum_rpg.fx",
        "quantum_rpg.meters",
        "quantum_rpg.gridmap",
        "quantum_rpg.conditions",
        "quantum_rpg.tclfix",
        "quantum_rpg.items",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="QuantumRPG",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
