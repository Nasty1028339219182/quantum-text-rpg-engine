# Editor (1.2.0)

Same window as the player. No graphics.

```
python -m quantum_rpg
# then: Редактор / Новая игра

python -m quantum_rpg editor shadow_keep
```

| Left | Right |
|---|---|
| Game | title, intro, start room, player stats |
| Rooms | name, description, dark, items, npcs, exits (lock/key), search |
| Items | type, damage, use, light |
| NPCs | location, dialogue, shop rows, hostile |
| Dialogues | nodes, RU/EN text, numbered choices, goto/end |
| Quests / fights / recipes | forms |
| events.yaml / hooks.py | text |

Unknown YAML (traps, `on_enter`, containers) stays in **extra YAML** and is not deleted on save.

Buttons: **Сохранить**, **Проверить**, **Играть**, **В меню**.

New games go to `games/` (Python) or `%APPDATA%\quantum-rpg\games` (exe). Bundled games are copied there before editing.
