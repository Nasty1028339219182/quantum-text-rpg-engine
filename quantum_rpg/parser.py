"""Verb + object parser. Russian and English, including single-letter directions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .i18n import dir_id

# verb id -> aliases (lowercase)
VERBS: dict[str, list[str]] = {
    "look": [
        "look", "l", "осмотр", "осмотреться", "осмотрись", "глянуть", "смотреть",
        "осмотреть", "examine", "x", "изучить", "опиши", "describe",
    ],
    "go": ["go", "walk", "move", "идти", "иди", "пойти", "пройти", "двигаться"],
    "take": ["take", "get", "pick", "grab", "взять", "брать", "поднять", "pick up"],
    "drop": ["drop", "положить", "выбросить", "бросить", "оставить"],
    "use": ["use", "использовать", "применить", "выпить", "drink", "activate"],
    "equip": ["equip", "wear", "wield", "надеть", "экипировать", "вооружиться"],
    "unequip": ["unequip", "remove", "снять"],
    "inventory": ["inventory", "i", "inv", "инвентарь", "инв"],
    "talk": ["talk", "speak", "ask", "говорить", "поговорить", "сказать", "спросить"],
    "attack": ["attack", "kill", "hit", "fight", "атаковать", "ударить", "бить", "убить"],
    "search": ["search", "искать", "обыскать", "поиск", "оглядеться"],
    "open": ["open", "открыть"],
    "close": ["close", "закрыть"],
    "read": ["read", "читать", "прочитать"],
    "give": ["give", "дать", "отдать"],
    "buy": ["buy", "купить"],
    "sell": ["sell", "продать"],
    "shop": ["shop", "магазин", "лавка", "торговля"],
    "craft": ["craft", "создать", "скрафтить", "варить", "brew"],
    "combine": ["combine", "соединить", "смешать"],
    "stats": ["stats", "status", "sheet", "я", "характеристики", "статы", "статус"],
    "quests": ["quests", "quest", "задания", "квесты", "задание"],
    "journal": ["journal", "log", "журнал"],
    "rumors": ["rumors", "rumour", "слухи", "слух"],
    "map": ["map", "карта"],
    "meters": ["meters", "meter", "шкалы", "шкала"],
    "note": ["note", "notes", "пометка", "пометки"],
    "scene": ["scene", "scenes", "сцена", "сцены"],
    "check": ["check", "validate", "проверить", "проверка"],
    "travel": ["travel", "ride", "ехать", "дорога", "путь"],
    "party": ["party", "отряд", "спутники"],
    "order": ["order", "приказ", "прикажи"],
    "reputation": ["reputation", "rep", "репутация", "фракции"],
    "sound": ["sound", "mute", "unmute", "звук", "музыка"],
    "volume": ["volume", "vol", "громкость"],
    "rest": ["rest", "sleep", "отдохнуть", "спать"],
    "wait": ["wait", "ждать"],
    "save": ["save", "сохранить", "сейв"],
    "load": ["load", "загрузить"],
    "help": ["help", "помощь", "?", "хелп", "команды"],
    "quit": ["quit", "exit", "q", "выход", "выйти", "сдаться"],
    "language": ["language", "lang", "язык"],
    "say": ["say", "произнести", "имя", "name"],
    "put": ["put", "вложить"],
}


@dataclass
class Command:
    verb: str
    args: list[str]
    raw: str
    argstr: str
    direction: Optional[str] = None


def _strip_prepositions(tokens: list[str]) -> list[str]:
    skip = {
        "the", "a", "an", "to", "at", "on", "in", "with", "from", "into",
        "в", "на", "к", "с", "со", "у", "от", "по", "из", "о", "об", "про",
    }
    return [t for t in tokens if t not in skip]


def parse(line: str) -> Optional[Command]:
    raw = (line or "").strip()
    if not raw:
        return None
    low = raw.lower()
    tokens = low.split()
    if not tokens:
        return None

    # bare direction
    d = dir_id(tokens[0]) if len(tokens) == 1 else None
    if d:
        return Command(verb="go", args=[d], raw=raw, argstr=d, direction=d)

    # two-word verbs first
    two = " ".join(tokens[:2]) if len(tokens) >= 2 else ""
    verb = None
    rest_tokens: list[str] = []

    if two in {"pick up", "look at", "go to"}:
        mapping = {"pick up": "take", "look at": "look", "go to": "go"}
        verb = mapping[two]
        rest_tokens = tokens[2:]
    else:
        for vid, aliases in VERBS.items():
            if tokens[0] in aliases:
                verb = vid
                rest_tokens = tokens[1:]
                break

    if verb is None:
        # "north door" etc. already handled; unknown word
        if dir_id(tokens[0]):
            verb = "go"
            rest_tokens = tokens
        else:
            return Command(verb="unknown", args=tokens, raw=raw, argstr=low)

    rest_tokens = _strip_prepositions(rest_tokens)
    argstr = " ".join(rest_tokens)
    direction = None
    if verb == "go":
        if rest_tokens:
            direction = dir_id(rest_tokens[0]) or dir_id(argstr)
        elif dir_id(tokens[0]) and tokens[0] not in VERBS["go"]:
            direction = dir_id(tokens[0])
    return Command(verb=verb, args=rest_tokens, raw=raw, argstr=argstr, direction=direction)
