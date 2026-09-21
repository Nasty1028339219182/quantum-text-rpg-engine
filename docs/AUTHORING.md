# Authoring a game (copy, paste, replace)

A game is a folder of YAML files. You do not edit the engine.

```bash
python -m quantum_rpg new dungeon1
```

Player-facing text:

```yaml
name: {ru: Ржавый меч, en: Rusty sword}
```

or a single string used for every language.

The Russian guide has the same snippets, more examples, and the full copy-paste cookbook:

**[docs/AUTHORING.ru.md](AUTHORING.ru.md)** (recommended — it is the complete version)

**[docs/YAML_REFERENCE.md](YAML_REFERENCE.md)** — every field

**[docs/HOOKS.md](HOOKS.md)** — optional Python

Minimal skeleton after `new`:

1. Set `start.location` in `game.yaml` to a room id.
2. Add rooms in `locations.yaml` with `exits: {north: other_id}`.
3. Add items in `items.yaml`. List their ids on the room: `items: [torch]`.
4. Add an NPC + a dialogue with the same id.
5. `python -m quantum_rpg validate dungeon1`
6. `python -m quantum_rpg play dungeon1`

Win the game by setting a flag the `win:` block looks for:

```yaml
win:
  flags: [boss_dead]
```

```yaml
# on the boss encounter
on_win:
  - set_flag: boss_dead
```

Look at `games/shadow_keep/` for a full dungeon using every system.
