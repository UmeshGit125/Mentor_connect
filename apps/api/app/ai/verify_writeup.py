"""Gate for the live write-up: an item survives only if its quote really is in the notes."""

import re

from app.schemas import WriteupContent

MAX_ITEMS = 5
MIN_QUOTE_CHARS = 3
MAX_TEXT_CHARS = 300
SECTIONS = ("discussed", "work_on", "next_steps")


def normalise(text: str) -> str:
    """Case and whitespace insensitive form used to compare quotes with notes."""
    return " ".join(text.casefold().split())


def verify_writeup(raw: dict, notes: str) -> WriteupContent:
    """Keeps items shaped {text, quote} whose quote is found in the notes. Returns plain strings."""
    haystack = normalise(notes)
    kept: dict[str, list[str]] = {}
    for name in SECTIONS:
        items = raw.get(name)
        kept[name] = []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            text, quote = item.get("text"), item.get("quote")
            if not isinstance(text, str) or not isinstance(quote, str):
                continue
            text = re.sub(r"\s+", " ", text).strip()
            needle = normalise(quote)
            if not text or len(text) > MAX_TEXT_CHARS or len(needle) < MIN_QUOTE_CHARS:
                continue
            if needle in haystack and text not in kept[name]:
                kept[name].append(text)
        kept[name] = kept[name][:MAX_ITEMS]
    return WriteupContent(**kept)
