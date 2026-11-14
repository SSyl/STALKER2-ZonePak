"""Text overrides: text/<culture>.toml files and the localization database export body."""
from __future__ import annotations

import struct
import tomllib
from pathlib import Path
from typing import Callable

# Index = ELocalizationLanguage value, and the name-map slot uasset.py writes for it in the same order.
CULTURES = ['ar', 'zh-Hans', 'zh-Hant', 'cs', 'en', 'fr', 'de', 'it', 'ja', 'ko', 'pl', 'pt-BR', 'ru', 'sr',
            'es', 'es-419', 'tr', 'uk']


class TextError(ValueError):
    def __init__(self, file: str, message: str):
        super().__init__(f'{file}: {message}')
        self.file = file
        self.message = message


def load_text(text_dir: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    if not text_dir.is_dir():
        return entries
    for f in sorted(text_dir.glob('*.toml')):
        if f.stem not in CULTURES:
            raise TextError(f.name, f'unknown culture {f.stem!r}. Use one of: {", ".join(CULTURES)}')
        try:
            table = tomllib.loads(f.read_text(encoding='utf-8-sig'))
        except UnicodeDecodeError as e:
            raise TextError(f.name, 'not UTF-8 text') from e
        except tomllib.TOMLDecodeError as e:
            raise TextError(f.name, str(e)) from e
        for key, text in table.items():
            if not key:
                raise TextError(f.name, 'empty key')
            if not isinstance(text, str):
                raise TextError(f.name, f'{key} must be a string. Quote keys that contain dots.')
            entries.setdefault(key, {})[f.stem] = text
    return entries


def gaps(entries: dict[str, dict[str, str]], game_keys: dict[str, str], copy_new_text: str) -> dict[str, list[str]]:
    """The cultures each new key, one the game lacks, still has no text for after fill_cultures."""
    out = {}
    for key, texts in entries.items():
        # In game on 2026-11-14, a key the game has, overridden only in ru and uk, showed the game's own en text.
        if key in game_keys:
            continue
        if key not in game_keys and copy_new_text in texts:
            continue
        missing = [c for c in CULTURES if c not in texts]
        if missing:
            out[key] = missing
    return out


def fill_cultures(entries: dict[str, dict[str, str]], game_text: Callable[[str], dict[str, str]],
                  fill_game_text: bool, copy_new_text: str) -> tuple[dict[str, dict[str, str]], int, int]:
    """Fills the cultures a text file leaves out. Returns the entries, texts taken from the game, texts copied.

    A key the game has gets the game's own text in each culture the mod leaves out, or the game's en text where the
    game has none, when fill_game_text is on. A new key gets the copy_new_text culture's text when it has one.
    """
    game_en = game_text('en')
    filled, from_game, copied = {}, 0, 0
    for key, texts in entries.items():
        full = dict(texts)
        for culture in CULTURES:
            if culture in full:
                continue
            if key in game_en and fill_game_text:
                full[culture] = game_text(culture).get(key, game_en[key])
                from_game += 1
            elif key not in game_en and copy_new_text in texts:
                full[culture] = texts[copy_new_text]
                copied += 1
        filled[key] = full
    return filled, from_game, copied


def _fstring(s: str) -> bytes:
    if not s:
        return struct.pack('<i', 0)
    if s.isascii():
        b = s.encode('ascii') + b'\0'
        return struct.pack('<i', len(b)) + b
    b = s.encode('utf-16-le') + b'\0\0'
    return struct.pack('<i', -(len(b) // 2)) + b


def export_body(entries: dict[str, dict[str, str]]) -> bytes:
    """Unversioned TMap<FString, TMap<ELocalizationLanguage, FString>>, as the Zone Kit cooks it."""
    out = bytearray(struct.pack('<Hii', 0x0300, 0, len(entries)))
    for key in sorted(entries):
        texts = sorted((CULTURES.index(c), t) for c, t in entries[key].items())
        out += _fstring(key) + struct.pack('<Hii', 0x0300, 0, len(texts))
        for index, text in texts:
            out += struct.pack('<II', index, 0) + _fstring(text)
    out += bytes(4)
    return bytes(out)
