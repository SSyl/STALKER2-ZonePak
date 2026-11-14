"""Reads the game's own text, one Game.locres per culture in pakchunk0-Windows.pak."""
from __future__ import annotations

import struct
from pathlib import Path

from . import tools

LOCRES_PATH = 'Stalker2/Content/Localization/Game/{culture}/Game.locres'


class LocresError(ValueError):
    pass


def _fstring(data: bytes, pos: int) -> tuple[str, int]:
    n = struct.unpack_from('<i', data, pos)[0]
    pos += 4
    if n >= 0:
        return data[pos:pos + n - 1].decode('latin-1') if n else '', pos + n
    return data[pos:pos - 2 * n - 2].decode('utf-16-le'), pos - 2 * n


def parse(data: bytes) -> dict[str, str]:
    """Key -> text for every key in a version 2 or 3 .locres (UE 4.20 and later)."""
    version = data[16] if len(data) > 16 else -1
    if version not in (2, 3):
        raise LocresError(f'unsupported .locres version {version}')
    strings_at = struct.unpack_from('<q', data, 17)[0]
    count = struct.unpack_from('<i', data, strings_at)[0]
    texts, pos = [], strings_at + 4
    for _ in range(count):
        text, pos = _fstring(data, pos)
        texts.append(text)
        pos += 4  # reference count
    out: dict[str, str] = {}
    pos = 17 + 8 + 4  # strings offset, entry count
    namespaces = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    for _ in range(namespaces):
        _, pos = _fstring(data, pos + 4)  # namespace hash, namespace
        keys = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        for _ in range(keys):
            key, pos = _fstring(data, pos + 4)  # key hash, key
            index = struct.unpack_from('<i', data, pos + 4)[0]  # source string hash, string index
            pos += 8
            out[key] = texts[index]
    return out


class GameText:
    """Loads each culture's Game.locres from the game install on first use."""

    def __init__(self, repak: Path, game: Path):
        self.repak = repak
        self.pak = game / 'Stalker2/Content/Paks/pakchunk0-Windows.pak'
        self._cultures: dict[str, dict[str, str]] = {}

    def culture(self, culture: str) -> dict[str, str]:
        if culture not in self._cultures:
            data = tools.pak_get(self.repak, self.pak, LOCRES_PATH.format(culture=culture))
            try:
                self._cultures[culture] = parse(data)
            except (LocresError, struct.error, IndexError, UnicodeDecodeError) as e:
                raise LocresError(f'{culture} Game.locres in {self.pak}: {e}') from e
        return self._cultures[culture]
