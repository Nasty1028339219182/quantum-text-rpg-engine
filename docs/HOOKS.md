# Optional Python hooks

Put `hooks.py` next to your YAML. If the file is missing, the game still runs.

Copy from `games/shadow_keep/hooks.py` or `games/template/hooks.py`.

```python
def on_load(game):
    """After YAML is loaded, before the intro."""

def on_turn(game):
    """End of every successful command."""

def on_enter(game, location_id):
    pass

def on_leave(game, location_id):
    pass

def on_use_item(game, item_id, target):
    """Return True if you fully handled the use."""
    return False

def on_talk(game, npc_id):
    """Return True to skip the YAML dialogue."""
    return False

def on_combat_start(game, encounter_id):
    pass

def on_combat_end(game, encounter_id, won: bool):
    pass

def on_command(game, verb, args):
    """Return True if you handled this verb (including 'say')."""
    return False

def on_ending(game, kind):
    """kind is 'win' or 'lose'."""
```

YAML can also call a function by name:

```yaml
effects:
  - hook: my_function
```

```python
def my_function(game, **kwargs):
    game.say("custom")
    game.state.flags.add("did_it")
```

## Useful `game` methods

```python
game.say("text")
game.has_flag("x")
game.has_item("iron_key")
game.give_item("torch")
game.take_from_inv("torch")
game.move_to("cellar")
game.start_combat("giant_rat")
game.finish("win")          # or "lose"
game.lang                   # "ru" or "en"
game.state.player.hp
game.state.flags            # set of str
game.state.location
```

Keep YAML for data. Use hooks only when a rule is awkward as data (true names, special items in combat, puzzles with counting).
