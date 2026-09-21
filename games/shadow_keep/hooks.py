"""Optional logic the YAML cannot express cleanly.

Copy this file into your own game and rename the functions you need.
Every function is optional. Returning True from on_command / on_use_item
means "I handled it, skip the default".
"""


def on_load(game):
    return None


def on_command(game, verb, args):
    if verb != "say":
        return False
    text = " ".join(args).lower()
    if "варгос" not in text and "vargos" not in text:
        return False
    lang = game.lang
    if "know_true_name" not in game.state.flags:
        game.say(
            "Имя без знания — только звук."
            if lang == "ru"
            else "A name without knowledge is only noise."
        )
        return True
    game.state.flags.add("true_name_spoken")
    if game.in_combat and game.combat_id == "vargos":
        game.say(
            "Имя садится в дым, как гвоздь. Варгос сжимается, плоть проявляется."
            if lang == "ru"
            else "The name drives into the smoke like a nail. Vargos tightens. Flesh shows."
        )
    elif game.state.location == "sanctum":
        game.say(
            "Ты произносишь имя. Воздух густеет. Теперь его можно ранить."
            if lang == "ru"
            else "You speak the name. The air thickens. Now it can be wounded."
        )
    else:
        game.say(
            "Имя уходит в камень. Здесь его некому слышать. Скажи его в святилище."
            if lang == "ru"
            else "The name sinks into stone. No one here can hear it. Speak it in the sanctum."
        )
        game.state.flags.discard("true_name_spoken")
    return True


def on_use_item(game, item_id, target):
    if item_id != "holy_water":
        return False
    lang = game.lang
    if game.in_combat and game.combat_id == "vargos":
        game.state.flags.add("demon_weak")
        game.take_from_inv("holy_water", silent=True)
        game.say(
            "Вода вспыхивает на дыму. Варгос орёт без рта. Дальше — клинок."
            if lang == "ru"
            else "The water flares on the smoke. Vargos screams without a mouth. Next — the blade."
        )
        return True
    if game.in_combat and game.combat_id == "skeleton":
        game.say(
            "Вода шипит на костях, но этого мало. Не трать её здесь."
            if lang == "ru"
            else "The water hisses on bone, but it is not enough. Do not spend it here."
        )
        return True
    game.say(
        "Святая вода. Против живых — просто вода. Береги для тени."
        if lang == "ru"
        else "Holy water. Against the living — only water. Keep it for the shadow."
    )
    return True
