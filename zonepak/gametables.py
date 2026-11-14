"""The game's own tables, decoded from the binary .cfg.bin files in its paks."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from . import bin2cfg, cfg, tools
from .build import game_dir
from .project import Config

# Part -> (its pak relative to the game folder, and the folder its tables sit under inside the pak). Deluxe,
# Ultimate and PreOrder ship inside the main game's paks, and Cost of Hope (DLC1) in its own game folder.
PARTS = {
    'base': ('Stalker2/Content/Paks/pakchunk0-Windows.pak', 'Stalker2/Content/GameLite/GameData/'),
    'PreOrder': ('Stalker2/Content/Paks/pakchunk101-Windows.pak', 'Stalker2/Content/GameLite/DLCGameData/PreOrder/'),
    'Deluxe': ('Stalker2/Content/Paks/pakchunk102-Windows.pak', 'Stalker2/Content/GameLite/DLCGameData/Deluxe/'),
    'Ultimate': ('Stalker2/Content/Paks/pakchunk104-Windows.pak', 'Stalker2/Content/GameLite/DLCGameData/Ultimate/'),
    'DLC1': ('DLC1/S2_DLC1Stalker2-Windows.pak', 'Stalker2/Content/GameLite/DLCGameData/DLC1/'),
}


@lru_cache(maxsize=None)
def _listing(repak: Path, pak: Path) -> frozenset[str]:
    return frozenset(tools.pak_list(repak, pak))


def table_text(config: Config, part: str, table: str) -> str | None:
    """`table`, such as 'ItemPrototypes' or 'WeaponData/WeaponGeneralSetupPrototypes', as cfg text. None when that
    part of the game is not installed or has no such table."""
    pak_rel, folder = PARTS[part]
    pak = game_dir(config) / pak_rel
    if not pak.is_file():
        return None
    repak, entry = config.require('repak'), f'{folder}{table}.cfg.bin'
    if entry not in _listing(repak, pak):
        return None
    roots = bin2cfg.read_binary_cfg(tools.pak_get(repak, pak, entry))
    known = {root.__internal__.rawName: root for root in roots if root.__internal__.rawName}
    return '\n'.join(root.to_string(known) for root in roots)


def table(config: Config, part: str, table: str) -> list:
    """`table` parsed with zonepak.cfg, or an empty list when table_text has none."""
    text = table_text(config, part, table)
    return cfg.parse(text, f'{part}/{table}', strict=False) if text is not None else []
