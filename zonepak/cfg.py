"""Parser and writer for S.T.A.L.K.E.R. 2 GameData cfg text."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_STRUCT = re.compile(r'^(?P<name>.+?)\s*:\s*struct\.begin\b\s*(?:\{(?P<flags>[^}]*)\})?')
_REMOVE = re.compile(r'^(?P<name>.+?)\s*:\s*removenode\s*$')
_VALUE = re.compile(r'^(?P<key>[^=]+?)\s*=\s*(?P<value>.*)$')


class CfgError(ValueError):
    def __init__(self, path: str, line: int, message: str):
        super().__init__(f'{path}:{line}: {message}')
        self.path, self.line, self.message = path, line, message


@dataclass
class Value:
    key: str
    value: str
    line: int = 0


@dataclass
class Remove:
    key: str
    line: int = 0


@dataclass
class Unknown:
    text: str
    line: int = 0


@dataclass
class Struct:
    name: str
    flags: dict[str, str | None] = field(default_factory=dict)
    children: list[Struct | Value | Remove | Unknown] = field(default_factory=list)
    line: int = 0

    @property
    def bpatch(self) -> bool:
        return 'bpatch' in self.flags

    def find(self, key: str) -> Struct | Value | Remove | None:
        for child in reversed(self.children):
            if isinstance(child, Struct) and child.name == key:
                return child
            if isinstance(child, (Value, Remove)) and child.key == key:
                return child
        return None


def _parse_flags(raw: str | None) -> dict[str, str | None]:
    flags: dict[str, str | None] = {}
    for part in (raw or '').split(';'):
        part = part.strip()
        if not part:
            continue
        key, sep, value = part.partition('=')
        flags[key.strip()] = value.strip() if sep else None
    return flags


def _lines(text: str):
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split('//', 1)[0].strip()
        if line.startswith('struct.end'):
            rest = line[len('struct.end'):].strip()
            if _STRUCT.match(rest):
                yield number, 'struct.end'
                line = rest
        if line:
            yield number, line


def parse(text: str, path: str = '<cfg>', strict: bool = True) -> list[Struct | Value | Remove | Unknown]:
    if text.startswith('\ufeff'):
        text = text[1:]
    roots: list[Struct | Value | Remove | Unknown] = []
    stack: list[Struct] = []
    for number, line in _lines(text):
        # Some vanilla files are unbalanced. With strict=False a stray struct.end is skipped,
        # and structs still open at end of file are returned as they are.
        if line == 'struct.end':
            if stack:
                stack.pop()
            elif strict:
                raise CfgError(path, number, 'struct.end without a matching struct.begin')
            continue
        target = stack[-1].children if stack else roots
        m = _STRUCT.match(line)
        if m:
            node = Struct(m['name'].strip(), _parse_flags(m['flags']), line=number)
            target.append(node)
            stack.append(node)
            continue
        m = _REMOVE.match(line)
        if m:
            target.append(Remove(m['name'].strip(), number))
            continue
        m = _VALUE.match(line)
        if m:
            target.append(Value(m['key'].strip(), m['value'].strip(), number))
            continue
        target.append(Unknown(line, number))
    if stack and strict:
        raise CfgError(path, stack[-1].line, f'struct.begin for {stack[-1].name} is never closed')
    return roots


def dumps(nodes: list, indent: str = '   ', newline: str = '\r\n') -> str:
    out: list[str] = []

    def emit(node, depth):
        pad = indent * depth
        if isinstance(node, Struct):
            flags = ';'.join(k if v is None else f'{k}={v}' for k, v in node.flags.items())
            out.append(f'{pad}{node.name} : struct.begin' + (f' {{{flags}}}' if flags else ''))
            for child in node.children:
                emit(child, depth + 1)
            out.append(f'{pad}struct.end')
        elif isinstance(node, Value):
            out.append(f'{pad}{node.key} = {node.value}' if node.value else f'{pad}{node.key} =')
        elif isinstance(node, Remove):
            out.append(f'{pad}{node.key} : removenode')
        else:
            out.append(f'{pad}{node.text}')

    for node in nodes:
        emit(node, 0)
    return newline.join(out) + newline


def canonical(nodes: list) -> tuple:
    def c(node):
        if isinstance(node, Struct):
            return 'S', node.name, tuple(node.flags.items()), tuple(c(x) for x in node.children)
        if isinstance(node, Value):
            return 'V', node.key, node.value
        if isinstance(node, Remove):
            return 'R', node.key
        return 'U', node.text

    return tuple(c(n) for n in nodes)
