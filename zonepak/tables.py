"""Which vanilla GameData and DLC tables the game ships, and where a patch for each must go."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

GAME_DATA = 'Stalker2/Content/GameLite/GameData/'
DLC_GAME_DATA = 'Stalker2/Content/GameLite/DLCGameData/'
PLAIN_PATCH = re.compile(r'^(?P<file>.+\.cfg)_patch_.+$')


@dataclass(frozen=True)
class Target:
    kind: str
    table: str


@dataclass(frozen=True)
class Tables:
    binarized: frozenset[str]
    plain: frozenset[str]

    @classmethod
    def from_pak_listing(cls, entries: Iterable[str], prefix: str = GAME_DATA) -> Tables:
        binarized, plain = set(), set()
        for entry in entries:
            entry = entry.strip().replace('\\', '/')
            if not entry.startswith(prefix):
                continue
            rel = entry[len(prefix):]
            if rel.endswith('.cfg.bin'):
                binarized.add(rel[:-len('.cfg.bin')])
            elif rel.endswith('.cfg'):
                plain.add(rel[:-len('.cfg')])
        return cls(frozenset(binarized), frozenset(plain))

    def _outermost_binarized(self, parts: tuple[str, ...]) -> Target | None:
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            if prefix in self.binarized:
                return Target('binarized', prefix)
        return None

    def vanilla_target(self, rel: str) -> Target | None:
        parts = PurePosixPath(rel).with_suffix('').parts
        found = self._outermost_binarized(parts)
        if found:
            return found
        whole = '/'.join(parts)
        return Target('plain', whole) if whole in self.plain else None

    def patch_target(self, rel: str) -> Target | None:
        path = PurePosixPath(rel)
        binarized = self._outermost_binarized(path.parent.parts)
        if binarized:
            return binarized if path.suffix == '.cfg' else None
        m = PLAIN_PATCH.match(path.name)
        if m:
            table = (path.parent / m['file']).as_posix()[:-len('.cfg')]
            return Target('plain', table) if table in self.plain else None
        return None


def describe(tables: Tables, root: str = 'cfg/GameData') -> list[str]:
    """The `zonepak tables` listing, with root as the patch folder shown in the headings."""
    return ([f'Binarized tables (patch with {root}/<Table>/<any name>.cfg):']
            + [f'  {table}' for table in sorted(tables.binarized, key=str.casefold)]
            + ['', f'Plain cfg files (patch with {root}/<File>.cfg_patch_<any name>):']
            + [f'  {name}.cfg' for name in sorted(tables.plain, key=str.casefold)])
