# Window UI (1.1.0)

No graphics. A log, a status line, buttons, a command box.

```
python -m quantum_rpg
python -m quantum_rpg gui --lang en
python -m quantum_rpg play shadow_keep --ui tk
```

Windows player: `QuantumRPG.exe` from the GitHub release.

| Area | What it does |
|---|---|
| Log | All game text |
| Status | Location, HP, gold |
| Exits | Click to walk |
| Items / people | Take, talk, attack, shop |
| Actions | Look, search, rest, quests, map |
| Inventory | Click an item, then examine / use / equip / drop |
| Combat / dialogue | Numbered buttons replace the room panel |
| Command line | Type `взять ключ` / `go north` as in 1.0.0 |

Saves: `save` / `load` in the top bar. Frozen exe writes to `%APPDATA%\quantum-rpg\saves`.

Editor: [EDITOR.md](EDITOR.md). Launcher buttons **Редактор** and **Новая игра**.
