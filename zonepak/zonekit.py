"""Which Zone Kit install zone_kit points at, and the level ZonePak works at."""
from __future__ import annotations

from pathlib import Path

from .project import KIT_LEVELS, Config, ProjectError

GAME_DATA = 'Stalker2/Content/GameLite/GameData'
# Installed by the Epic launcher's "Zone Kit editor" option. Stock UE's Engine/Binaries/Win64/UnrealEditor-Cmd.exe
# is absent from every Zone Kit install, the full one included.
FULL_EDITOR = ('Stalker2/Binaries/Win64/Stalker2ModEditor-Win64-Shipping-Cmd.exe',
               'Stalker2/Content/Paks/FullEditor-WindowsModEditor.pak')


def detect(kit: Path | None) -> str:
    if kit is None:
        return 'none'
    if not (kit / GAME_DATA).is_dir():
        raise ProjectError(f'{kit / GAME_DATA} not found. Is zone_kit set to the Zone Kit install folder?')
    return 'full' if all((kit / f).is_file() for f in FULL_EDITOR) else 'lesser'


def level(config: Config) -> str:
    mode = config.zone_kit_mode
    if mode == 'none':
        return mode
    found = detect(config.zone_kit)
    if mode is None:
        return found
    if KIT_LEVELS.index(mode) > KIT_LEVELS.index(found):
        where = f'{config.zone_kit} is the {found} Zone Kit' if config.zone_kit else 'zone_kit is not set'
        raise ProjectError(f'zone_kit_mode = {mode}, but {where}. zone_kit_mode can only lower the level ZonePak '
                           'detects, so remove it or set a lower one')
    return mode


def require(config: Config, needed: str, purpose: str) -> Path:
    """The Zone Kit folder, when the level ZonePak works at is `needed` or higher."""
    kit = config.require('zone_kit')
    used = level(config)
    if KIT_LEVELS.index(used) < KIT_LEVELS.index(needed):
        if config.zone_kit_mode:
            raise ProjectError(f'{purpose} needs the {needed} Zone Kit or higher, and zone_kit_mode = '
                               f'{config.zone_kit_mode} keeps ZonePak from using {kit}')
        raise ProjectError(f'{purpose} needs the {needed} Zone Kit, and {kit} is the {used} one')
    return kit


def report(config: Config) -> str:
    """One line for check and build output. Never raises, so a bad zone_kit only fails what needs the kit."""
    try:
        used = level(config)
    except ProjectError as e:
        return f'Zone Kit: not usable. {e}'
    if config.zone_kit is None:
        return 'Zone Kit: none (zone_kit is not set)'
    if config.zone_kit_mode == 'none':
        return f'Zone Kit: none ({config.zone_kit} ignored because zone_kit_mode = none)'
    found = detect(config.zone_kit)
    if found != used:
        return f'Zone Kit: {used} ({found} install at {config.zone_kit}, lowered by zone_kit_mode)'
    return f'Zone Kit: {used} ({config.zone_kit})'
