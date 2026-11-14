"""zonepak.toml, `zonepak new`, and the per-user tool configuration."""
from __future__ import annotations

import os
import re
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Callable

from . import fetch
from .locdb import CULTURES

PROJECT_FILE = 'zonepak.toml'
NAME_RE = re.compile(r'[A-Za-z0-9_]+')
# build() writes the mod to build/<name>/ next to its own build/stage/.
RESERVED_NAMES = ('stage',)
PROJECT_KEYS = ('name', 'friendly_name', 'description', 'version', 'database_id', 'author', 'website', 'nexus_id',
                'fill_game_text', 'copy_new_text', 'group', 'option')
GROUP_KEYS = ('name', 'select')
# FOMOD group types: "any" lets the player tick any number of options, "one" exactly one.
GROUP_SELECT = {'any': 'SelectAny', 'one': 'SelectExactlyOne'}
# The wizard group that holds options without a group key.
DEFAULT_GROUP = 'Options'
OPTION_KEYS = ('name', 'folder', 'description', 'image', 'default', 'group', 'empty')
# Main and fomod are folders at the root of the FOMOD zip, next to the option folders.
RESERVED_FOLDERS = ('cfg', 'text', 'build', 'main', 'fomod')
IMAGE_SUFFIXES = ('.png', '.jpg')
# \d would also match full-width and other Unicode digits, which Vortex's version parser rejects.
VERSION_RE = re.compile(r'[0-9]+(\.[0-9]+){0,2}')
CONFIG_KEYS = ('zone_kit', 'game', 'repak', 'retoc')
# Anything outside XML 1.0's Char production. ElementTree writes these characters unescaped, and the FOMOD files
# then fail to parse.
NOT_XML_CHAR = re.compile('[^\t\n\r\u0020-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]')


class ProjectError(ValueError):
    pass


@dataclass(frozen=True)
class Group:
    name: str
    select: str = 'any'


@dataclass(frozen=True)
class Option:
    root: Path
    name: str
    folder: str
    description: str = ''
    image: Path | None = None
    default: bool = False
    group: str = DEFAULT_GROUP
    empty: bool = False

    @property
    def cfg_dir(self) -> Path:
        return self.root / 'cfg'


@dataclass(frozen=True)
class Project:
    root: Path
    name: str
    friendly_name: str
    description: str
    version: str
    database_id: str
    author: str = ''
    website: str = ''
    nexus_id: int | None = None
    options: tuple[Option, ...] = ()
    groups: tuple[Group, ...] = ()
    fill_game_text: bool = False
    copy_new_text: str = ''

    def option_groups(self) -> list[tuple[Group, list[Option]]]:
        """Each group that has options, with its options, in the order the groups first appear among the options."""
        declared = {g.name: g for g in self.groups}
        out: dict[str, tuple[Group, list[Option]]] = {}
        for option in self.options:
            group = declared.get(option.group, Group(option.group))
            out.setdefault(group.name, (group, []))[1].append(option)
        return list(out.values())

    @property
    def cfg_dir(self) -> Path:
        return self.root / 'cfg'

    @property
    def text_dir(self) -> Path:
        return self.root / 'text'

    @property
    def build_dir(self) -> Path:
        return self.root / 'build'


def _check_name(name: str) -> None:
    if not NAME_RE.fullmatch(name):
        raise ProjectError(f'mod name {name!r} must use only letters, digits and underscores')
    if name.lower() in RESERVED_NAMES:
        raise ProjectError(f'mod name {name!r} is reserved, because ZonePak uses build/{name.lower()}/ itself')


def _check_xml_text(where: str, field: str, value: str) -> None:
    bad = NOT_XML_CHAR.search(value)
    if bad:
        code = ord(bad[0])
        kind = 'a control character' if code < 0x20 else 'a character'
        raise ProjectError(f'{where}: {field} contains {kind} (U+{code:04X}) that the FOMOD files cannot hold. In '
                           'double quotes, a backslash starts an escape such as \\f. Use single quotes, or write '
                           '\\\\ for each backslash')


def _read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding='utf-8-sig'))
    except tomllib.TOMLDecodeError as e:
        raise ProjectError(f'{path}: {e}') from e


def load_project(root: Path) -> Project:
    path = root / PROJECT_FILE
    if not path.is_file():
        raise ProjectError(f'{path} not found. Run `python -m zonepak --project <parent folder> new <Name>` '
                           'to create a project.')
    data = _read_toml(path)
    unknown = set(data) - set(PROJECT_KEYS)
    if unknown:
        raise ProjectError(f'{path}: unknown keys {", ".join(sorted(unknown))}')
    name = str(data.get('name', ''))
    _check_name(name)
    database_id = str(data.get('database_id', ''))
    if not re.fullmatch(r'\d{10}', database_id):
        raise ProjectError(f'{path}: database_id must be 10 digits')
    # An unquoted version is a TOML float, and 1.10 would read back as 1.1.
    version = data.get('version', '1.0')
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ProjectError(f'{path}: version must be one to three numbers separated by dots, in quotes, '
                           'for example "1.0"')
    for key in ('author', 'website'):
        if not isinstance(data.get(key, ''), str):
            raise ProjectError(f'{path}: {key} must be text in quotes')
    nexus_id = data.get('nexus_id')
    # bool is a subclass of int, so nexus_id = true would otherwise pass as 1.
    if nexus_id is not None and (type(nexus_id) is not int or nexus_id < 1):
        raise ProjectError(f"{path}: nexus_id must be a whole number above 0, the number in the mod's Nexus URL")
    friendly_name, description = str(data.get('friendly_name', name)), str(data.get('description', ''))
    author, website = data.get('author', '').strip(), data.get('website', '').strip()
    for key, value in (('friendly_name', friendly_name), ('description', description), ('author', author),
                       ('website', website)):
        _check_xml_text(str(path), key, value)
    fill_game_text = data.get('fill_game_text', False)
    if not isinstance(fill_game_text, bool):
        raise ProjectError(f'{path}: fill_game_text must be true or false, without quotes')
    copy_new_text = data.get('copy_new_text', '')
    if copy_new_text != '' and copy_new_text not in CULTURES:
        raise ProjectError(f'{path}: copy_new_text must be a culture in quotes, one of {", ".join(CULTURES)}')
    groups = _load_groups(path, data.get('group', []))
    options = _load_options(root, path, data.get('option', []), groups)
    for group in groups:
        members = [o for o in options if o.group == group.name]
        if not members:
            raise ProjectError(f"{path}: group '{group.name}' has no options")
        if group.select == 'one' and sum(o.default for o in members) != 1:
            raise ProjectError(f"{path}: group '{group.name}' has select = \"one\", so exactly one of its options "
                               'needs default = true')
    return Project(root, name, friendly_name, description, version, database_id, author, website, nexus_id,
                   options, groups, fill_game_text, copy_new_text)


def _load_groups(path: Path, tables) -> tuple[Group, ...]:
    if not isinstance(tables, list) or not all(isinstance(t, dict) for t in tables):
        raise ProjectError(f'{path}: write each group as a table that starts with [[group]]')
    groups: list[Group] = []
    for number, table in enumerate(tables, 1):
        where = f'{path}: group {number}'
        unknown = set(table) - set(GROUP_KEYS)
        if unknown:
            raise ProjectError(f'{where}: unknown keys {", ".join(sorted(unknown))}')
        name = table.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ProjectError(f'{where}: name is required, as text in quotes')
        name = name.strip()
        _check_xml_text(where, 'name', name)
        if name.lower() == DEFAULT_GROUP.lower():
            raise ProjectError(f"{where}: name '{name}' is reserved for options without a group")
        for other_number, other in enumerate(groups, 1):
            if other.name.lower() == name.lower():
                raise ProjectError(f"{where}: name '{name}' is already used by group {other_number}")
        select = table.get('select', 'any')
        if select not in GROUP_SELECT:
            raise ProjectError(f'{where}: select must be "any" or "one"')
        groups.append(Group(name, select))
    return tuple(groups)


def _load_options(root: Path, path: Path, tables, groups: tuple[Group, ...] = ()) -> tuple[Option, ...]:
    if not isinstance(tables, list) or not all(isinstance(t, dict) for t in tables):
        raise ProjectError(f'{path}: write each option as a table that starts with [[option]]')
    options: list[Option] = []
    for number, table in enumerate(tables, 1):
        where = f'{path}: option {number}'
        unknown = set(table) - set(OPTION_KEYS)
        if unknown:
            raise ProjectError(f'{where}: unknown keys {", ".join(sorted(unknown))}')
        name = table.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ProjectError(f'{where}: name is required, as text in quotes')
        folder = table.get('folder')
        if not isinstance(folder, str) or not NAME_RE.fullmatch(folder):
            raise ProjectError(f'{where}: folder is required and must use only letters, digits and underscores')
        if folder.lower() in RESERVED_FOLDERS:
            raise ProjectError(f"{where}: folder '{folder}' is reserved. cfg, text, build, Main and fomod, in any "
                               'case, are taken')
        for other_number, other in enumerate(options, 1):
            if other.folder.lower() == folder.lower():
                raise ProjectError(f"{where}: folder '{folder}' is already used by option {other_number}")
        description = table.get('description', '')
        if not isinstance(description, str):
            raise ProjectError(f'{where}: description must be text in quotes')
        _check_xml_text(where, 'name', name)
        _check_xml_text(where, 'description', description)
        default = table.get('default', False)
        if not isinstance(default, bool):
            raise ProjectError(f'{where}: default must be true or false, without quotes')
        empty = table.get('empty', False)
        if not isinstance(empty, bool):
            raise ProjectError(f'{where}: empty must be true or false, without quotes')
        group = table.get('group', DEFAULT_GROUP)
        names = {g.name.lower(): g.name for g in groups}
        if group != DEFAULT_GROUP:
            if not isinstance(group, str) or group.strip().lower() not in names:
                raise ProjectError(f'{where}: group must be the name of a [[group]] table, in quotes')
            group = names[group.strip().lower()]
        image = _option_image(root, where, table.get('image'))
        for other_number, other in enumerate(options, 1):
            if image and other.image and other.image.name.lower() == image.name.lower() and other.image != image:
                raise ProjectError(f'{where}: image file name {image.name} is already used by the image of option '
                                   f'{other_number}. Rename one of the two files')
        if (root / folder / 'text').exists():
            raise ProjectError(f'{where}: options are cfg-only, so {folder}/text/ is not allowed. Put text in the '
                               "main part's text/ folder")
        options.append(Option(root / folder, name.strip(), folder, description.strip(), image, default, group, empty))
    return tuple(options)


def _option_image(root: Path, where: str, image) -> Path | None:
    if image is None:
        return None
    if not isinstance(image, str) or PurePath(image).suffix.lower() not in IMAGE_SUFFIXES:
        raise ProjectError(f'{where}: image must be the path of a .png or .jpg file, in quotes')
    _check_xml_text(where, 'image', image)
    if PurePath(image).anchor or '..' in PurePath(image).parts:
        raise ProjectError(f'{where}: image must be a path inside the project folder, such as "fomod/option.png"')
    if not (root / image).is_file():
        raise ProjectError(f'{where}: image {root / image} not found')
    return root / image


def new_project(parent: Path, name: str, now: Callable[[], float] = time.time) -> Path:
    _check_name(name)
    root = parent / name
    if root.exists():
        raise ProjectError(f'{root} already exists')
    (root / 'cfg' / 'GameData').mkdir(parents=True)
    (root / 'text').mkdir()
    (root / PROJECT_FILE).write_text(
        f'name = "{name}"\nfriendly_name = "{name}"\ndescription = ""\nauthor = ""\nwebsite = ""\n'
        f'version = "1.0"\ndatabase_id = "{int(now())}"\n', encoding='utf-8')
    (root / '.gitignore').write_text('build/\n', encoding='utf-8')
    return root


@dataclass(frozen=True)
class Config:
    zone_kit: Path | None = None
    game: Path | None = None
    repak: Path | None = None
    retoc: Path | None = None
    source: Path | None = None
    # True under ZonePak's own command line, whose flags the messages below may then suggest.
    cli: bool = False

    def require(self, key: str) -> Path:
        value = getattr(self, key)
        if value is None and key in fetch.DOWNLOADS:
            return fetch.ensure(key, cli=self.cli)
        if value is None:
            where = self.source or default_config_path()
            flag = f' or pass --{key.replace("_", "-")}' if self.cli else ''
            if not where.is_file():
                raise ProjectError(f'{key} is not set, and the config file {where} does not exist yet. Create it as '
                                   f'step 2 of the README quick start shows{"," if flag else ""}{flag}.')
            raise ProjectError(f'{key} is not set. Add it to {where}{flag}.')
        return value


def default_config_path() -> Path:
    appdata = os.environ.get('APPDATA')
    if appdata:
        return Path(appdata) / 'ZonePak' / 'config.toml'
    return Path.home() / '.config' / 'zonepak' / 'config.toml'


def load_config(path: Path | None = None, overrides: dict | None = None) -> Config:
    if path is None:
        path = default_config_path()
    elif not path.is_file():
        raise ProjectError(f'{path} not found')
    data = _read_toml(path) if path.is_file() else {}
    unknown = set(data) - set(CONFIG_KEYS)
    if unknown:
        raise ProjectError(f'{path}: unknown keys {", ".join(sorted(unknown))}')
    for key, value in data.items():
        if not isinstance(value, str) or not value:
            raise ProjectError(f'{path}: {key} must be a path string')
    data.update({k: v for k, v in (overrides or {}).items() if v is not None})
    return Config(**{k: Path(v) for k, v in data.items()}, source=path)
