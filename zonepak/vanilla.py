"""Index of the vanilla GameData tables from the Zone Kit, with refkey inheritance."""
from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import Path

from . import cfg
from .tables import Tables, Target


@dataclass
class Entry:
    table: Target
    file: str
    node: cfg.Struct


def _key(node) -> str | None:
    if isinstance(node, cfg.Struct):
        return node.name
    if isinstance(node, (cfg.Value, cfg.Remove)):
        return node.key
    return None


def _merge(base: cfg.Struct, own: cfg.Struct) -> cfg.Struct:
    if 'bskipref' in own.flags:
        return own
    children = list(base.children)
    for child in own.children:
        name = _key(child)
        index = next((i for i in reversed(range(len(children))) if name is not None and _key(children[i]) == name),
                     None)
        if isinstance(child, cfg.Remove):
            if index is not None:
                del children[index]
        elif index is None:
            children.append(child)
        elif isinstance(child, cfg.Struct) and isinstance(children[index], cfg.Struct):
            children[index] = _merge(children[index], child)
        else:
            children[index] = child
    return cfg.Struct(own.name, own.flags, children, own.line)


class Vanilla:
    def __init__(self, game_data: Path, tables: Tables):
        self.game_data = game_data
        self.tables = tables
        self._entries: dict[Target, dict[str, list[Entry]]] = {}
        self._file_roots: dict[str, list] = {}
        self._merged: dict[int, cfg.Struct] = {}

    def _files_of(self, target: Target) -> list[Path]:
        top = self.game_data / f'{target.table}.cfg'
        files = [top] if top.is_file() else []
        folder = self.game_data / target.table
        if target.kind == 'binarized' and folder.is_dir():
            files.extend(sorted(folder.rglob('*.cfg')))
        return files

    def _load(self, target: Target) -> dict[str, list[Entry]]:
        if target not in self._entries:
            index: dict[str, list[Entry]] = {}
            for f in self._files_of(target):
                rel = f.relative_to(self.game_data).as_posix()
                if self.tables.vanilla_target(rel) != target:
                    continue
                roots = cfg.parse(f.read_text(encoding='utf-8-sig'), rel, strict=False)
                self._file_roots[rel] = roots
                for node in roots:
                    if isinstance(node, cfg.Struct):
                        index.setdefault(node.name, []).append(Entry(target, rel, node))
            self._entries[target] = index
        return self._entries[target]

    def lookup(self, target: Target, sid: str) -> Entry | None:
        entries = self.lookup_all(target, sid)
        return entries[-1] if entries else None

    def lookup_all(self, target: Target, sid: str) -> list[Entry]:
        return self._load(target).get(sid, [])

    def parent_of(self, entry: Entry) -> Entry | None:
        refkey = entry.node.flags.get('refkey')
        if not refkey:
            return None
        file, target = entry.file, entry.table
        refurl = entry.node.flags.get('refurl')
        if refurl:
            if refurl.startswith('@BaseGame/'):
                file = refurl[len('@BaseGame/'):]
            else:
                file = posixpath.normpath(posixpath.join(posixpath.dirname(entry.file), refurl))
            if file.startswith('..'):
                return None
            target = self.tables.vanilla_target(file)
            if target is None:
                return None
        if refkey.startswith('['):
            self._load(target)
            for node in self._file_roots.get(file, []):
                if isinstance(node, cfg.Struct) and node.name == refkey:
                    return Entry(target, file, node)
            # NPCPrototypes also writes a bracketed SID ({refkey=[nikolaic]} on nikolaicM) that names the struct nikolaic.
            name = refkey[1:-1]
            return None if name.isdigit() else self.lookup(target, name)
        return self.lookup(target, refkey)

    def merged(self, entry: Entry) -> cfg.Struct:
        key = id(entry.node)
        if key in self._merged:
            return self._merged[key]
        self._merged[key] = entry.node
        parent = self.parent_of(entry)
        result = _merge(self.merged(parent), entry.node) if parent else entry.node
        self._merged[key] = result
        return result
