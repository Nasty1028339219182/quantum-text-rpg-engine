"""Item kinds. A weapon is not a book: the editor, the window, and equip all use this list."""

from __future__ import annotations

from typing import Optional

CATEGORIES = (
    {"id": "weapon", "label": "cat_weapon", "slot": "weapon", "equip": True},
    {"id": "armor", "label": "cat_armor", "slot": "armor", "equip": True},
    {"id": "shield", "label": "cat_shield", "slot": "shield", "equip": True},
    {"id": "accessory", "label": "cat_accessory", "slot": "accessory", "equip": True},
    {"id": "consumable", "label": "cat_consumable", "slot": "", "equip": False},
    {"id": "key", "label": "cat_key", "slot": "", "equip": False},
    {"id": "book", "label": "cat_book", "slot": "", "equip": False},
    {"id": "quest", "label": "cat_quest", "slot": "", "equip": False},
    {"id": "misc", "label": "cat_misc", "slot": "", "equip": False},
)

IDS = {row["id"] for row in CATEGORIES}
BY_ID = {row["id"]: row for row in CATEGORIES}

ALIASES = {
    "weapon": "weapon",
    "оружие": "weapon",
    "armor": "armor",
    "броня": "armor",
    "armour": "armor",
    "shield": "shield",
    "щит": "shield",
    "accessory": "accessory",
    "украшение": "accessory",
    "кольцо": "accessory",
    "consumable": "consumable",
    "зелье": "consumable",
    "еда": "consumable",
    "расходник": "consumable",
    "key": "key",
    "ключ": "key",
    "book": "book",
    "книга": "book",
    "quest": "quest",
    "задание": "quest",
    "квест": "quest",
    "misc": "misc",
    "разное": "misc",
    "прочее": "misc",
    "all": "",
    "все": "",
}


def item_kind(item: dict) -> str:
    kind = str((item or {}).get("type") or "misc")
    return kind if kind in IDS else "misc"


def category(kind: str) -> dict:
    return BY_ID.get(kind) or BY_ID["misc"]


def equip_slot(item: dict) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    if item.get("slot"):
        return str(item["slot"])
    row = category(item_kind(item))
    if row.get("equip") and row.get("slot"):
        return str(row["slot"])
    return None


def default_slot(kind: str) -> str:
    row = category(kind)
    return str(row["slot"]) if row.get("equip") else ""


def match_kind(word: str) -> Optional[str]:
    key = (word or "").strip().lower()
    if not key:
        return None
    if key not in ALIASES:
        return None
    return ALIASES[key]
