"""Validation of a project's patch files against the vanilla tables."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from . import cfg
from .tables import PLAIN_PATCH, Tables, Target
from .vanilla import Vanilla


@dataclass(frozen=True)
class Finding:
    level: str
    file: str
    line: int
    message: str
    # Findings that share a group print as one summary line naming each finding's item.
    group: str = ''
    item: str = ''

    def __str__(self) -> str:
        return f'{self.file}:{self.line}: {self.level}: {self.message}'


GROUP_SHOWN = 3


def summarize(findings: list[Finding]) -> list[str]:
    """The lines to print: each finding, except that a group of two or more prints as one line."""
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        if f.group:
            groups.setdefault(f.group, []).append(f)
    lines: list[str] = []
    for f in findings:
        members = groups.get(f.group, [])
        if len(members) < 2:
            lines.append(str(f))
        elif members[0] is f:
            items = list(dict.fromkeys(m.item for m in members))
            shown = ', '.join(items[:GROUP_SHOWN])
            if len(items) > GROUP_SHOWN:
                shown += f' and {len(items) - GROUP_SHOWN} others'
            count = f'{len(members)}' + (f' ({len(items)} SIDs)' if len(items) != len(members) else '')
            lines.append(f'{f.level}: {count} {f.group}: {shown}')
    return lines


def _is_index(key: str) -> bool:
    return key.startswith('[') and key.endswith(']')


def _check_patch(patch: cfg.Struct, own: cfg.Struct | None, merged: cfg.Struct, path: str, sid: str,
                 file: str, findings: list[Finding]) -> None:
    for child in patch.children:
        if isinstance(child, cfg.Unknown):
            continue
        key = child.name if isinstance(child, cfg.Struct) else child.key
        if _is_index(key):
            continue
        here = f'{path}.{key}'
        found = merged.find(key)
        if isinstance(child, cfg.Remove):
            if found is None:
                findings.append(Finding('warning', file, child.line, f'removenode on {here}, which does not exist'))
            continue
        if found is None:
            findings.append(Finding('error', file, child.line, f'{here} does not exist in vanilla'))
            continue
        if isinstance(child, cfg.Struct):
            if not isinstance(found, cfg.Struct):
                findings.append(Finding('error', file, child.line, f'{here} is a value in vanilla, not a struct'))
                continue
            own_child = own.find(key) if own is not None else None
            if not isinstance(own_child, cfg.Struct):
                own_child = None
            if child.bpatch:
                _check_patch(child, own_child, found, here, sid, file, findings)
        elif isinstance(found, cfg.Struct):
            findings.append(Finding('error', file, child.line, f'{here} is a struct in vanilla, not a value'))


def _check_unknown(nodes: list, file: str, findings: list[Finding]) -> None:
    for node in nodes:
        if isinstance(node, cfg.Unknown):
            findings.append(Finding('error', file, node.line, f'unrecognized line: {node.text}'))
        elif isinstance(node, cfg.Struct):
            _check_unknown(node.children, file, findings)


def _check_file(roots: list, target: Target, vanilla: Vanilla, file: str, defined: set[str],
                findings: list[Finding]) -> None:
    for node in roots:
        if isinstance(node, cfg.Unknown):
            continue
        if not isinstance(node, cfg.Struct):
            findings.append(Finding('warning', file, node.line, 'top-level line outside any struct'))
            continue
        entries = vanilla.lookup_all(target, node.name)
        if node.bpatch:
            if not entries and node.name in defined:
                # A new struct of this part or of the main part. Its fields are not checked.
                continue
            if not entries:
                findings.append(Finding('error', file, node.line,
                                        f'{node.name} does not exist in {target.table}. '
                                        'If it is a DLC item, put the patch under cfg/DLCGameData/<DLC>/.'))
                continue
            best: tuple[tuple[int, int], list[Finding]] | None = None
            for entry in entries:
                attempt: list[Finding] = []
                _check_patch(node, entry.node, vanilla.merged(entry), node.name, node.name, file, attempt)
                score = (sum(f.level == 'error' for f in attempt), len(attempt))
                if best is None or score <= best[0]:
                    best = (score, attempt)
            findings.extend(best[1])
        elif entries:
            findings.append(Finding('warning', file, node.line,
                                    f'{node.name} has no {{bpatch}} and replaces the whole vanilla struct'))
        else:
            refkey = node.flags.get('refkey')
            if (refkey and 'refurl' not in node.flags and not refkey.startswith('[')
                    and refkey not in defined and vanilla.lookup(target, refkey) is None):
                findings.append(Finding('error', file, node.line, f'refkey {refkey} does not exist in {target.table}'))


def _check_dlc_file(roots: list, dlc: str, file: str, findings: list[Finding]) -> None:
    for node in roots:
        if isinstance(node, cfg.Struct):
            findings.append(Finding('warning', file, node.line,
                                    f'{node.name} not checked: the Zone Kit has no {dlc} data',
                                    f'patches not checked, the Zone Kit has no {dlc} data', node.name))
        elif not isinstance(node, cfg.Unknown):
            findings.append(Finding('warning', file, node.line, 'top-level line outside any struct'))


OS_FILES = ('thumbs.db', 'desktop.ini', '.ds_store')


def is_os_file(path: Path) -> bool:
    return path.name.lower() in OS_FILES or path.name.startswith('.')


def _not_patch_named(file: str) -> Finding | None:
    path = PurePosixPath(file)
    if path.suffix == '.cfg' or PLAIN_PATCH.match(path.name):
        return None
    if path.name.lower().endswith('.cfg.txt'):
        return Finding('error', file, 0, 'Notepad saved this file as a text file. Rename it to end in .cfg '
                                         'instead of .cfg.txt')
    # A warning is enough only because build._patch_files uses the same filter and never packs these files.
    return Finding('warning', file, 0, 'not a .cfg or .cfg_patch_ file, so build does not pack it')


def _not_loaded(rel: str, tables: Tables, root: str) -> str:
    path = PurePosixPath(rel)
    if path.suffix == '.cfg':
        folder = path.parent.as_posix() if path.parent.parts else root
        return f'{folder} is not a binarized table in the game, so this file is not loaded'
    base = (path.parent / PLAIN_PATCH.match(path.name)['file']).as_posix()
    owner = tables.patch_target(base)
    if owner is not None and owner.kind == 'binarized':
        return (f'plain-cfg patches are not read inside a binarized table folder ({owner.table}), '
                'so this file is not loaded')
    return f'{base} is not a plain table in the game, so this patch is not loaded'


def _patch_root(file: str, dlc_tables: dict[str, Tables]) -> tuple[str, str | None] | None:
    if file.startswith('GameData/'):
        return 'GameData', None
    parts = file.split('/')
    if len(parts) > 2 and parts[0] == 'DLCGameData' and parts[1] in dlc_tables:
        return f'DLCGameData/{parts[1]}', parts[1]
    return None


def _scan(cfg_root: Path, tables: Tables, dlc_tables: dict[str, Tables]
          ) -> tuple[list[Finding], list[tuple[str, Target, list, str | None]]]:
    findings: list[Finding] = []
    parsed: list[tuple[str, Target, list, str | None]] = []
    if not cfg_root.is_dir():
        return findings, parsed
    for f in sorted(p for p in cfg_root.rglob('*') if p.is_file() and not is_os_file(p)):
        file = f.relative_to(cfg_root).as_posix()
        name_finding = _not_patch_named(file)
        if name_finding is not None:
            findings.append(name_finding)
            continue
        root = _patch_root(file, dlc_tables)
        if root is None:
            findings.append(Finding('error', file, 0, 'outside GameData and DLCGameData/<DLC>, '
                                                      'so the game does not load it as a patch'))
            continue
        root_name, dlc = root
        rel = file[len(root_name) + 1:]
        root_tables = dlc_tables[dlc] if dlc else tables
        target = root_tables.patch_target(rel)
        if target is None and rel.endswith('.cfg') and rel[:-len('.cfg')] in root_tables.plain:
            # Verified in-game 2026-11-03: a full CoreVariables.cfg at its vanilla path replaced the vanilla file.
            findings.append(Finding('warning', file, 0,
                                    f'replaces the whole vanilla {rel}, so other mods cannot patch it and game '
                                    f'updates to it are hidden. A {rel}_patch_<name> file changes only what it lists'))
            continue
        if target is None:
            findings.append(Finding('error', file, 0, _not_loaded(rel, root_tables, root_name)))
            continue
        try:
            roots = cfg.parse(f.read_text(encoding='utf-8-sig'), file)
        except UnicodeDecodeError:
            findings.append(Finding('error', file, 0, 'not UTF-8 text'))
            continue
        except cfg.CfgError as e:
            findings.append(Finding('error', file, e.line, e.message))
            continue
        parsed.append((file, target, roots, dlc))
    return findings, parsed


def _new_sids(parsed: list[tuple[str, Target, list, str | None]]) -> dict[Target, set[str]]:
    defined: dict[Target, set[str]] = {}
    for _, target, roots, dlc in parsed:
        if dlc is None:
            defined.setdefault(target, set()).update(n.name for n in roots if isinstance(n, cfg.Struct)
                                                     and not n.bpatch)
    return defined


def _set_paths(nodes: list, prefix: str = '') -> dict[str, int]:
    """Each field a patch file sets, as a dotted path, with its line. A struct without {bpatch} counts as one path,
    since it sets everything under it."""
    out: dict[str, int] = {}
    for node in nodes:
        if isinstance(node, cfg.Struct):
            path = f'{prefix}{node.name}'
            if node.bpatch:
                out.update(_set_paths(node.children, f'{path}.'))
            else:
                out[path] = node.line
        elif isinstance(node, (cfg.Value, cfg.Remove)):
            out[f'{prefix}{node.key}'] = node.line
    return out


def _overlap(paths: dict[str, int], others: dict[str, int]) -> tuple[str, int] | None:
    for path, line in paths.items():
        for other in others:
            if path == other or other.startswith(f'{path}.') or path.startswith(f'{other}.'):
                return path, line
    return None


def _child(node: cfg.Struct, key: str):
    for c in node.children:
        if (isinstance(c, cfg.Struct) and c.name == key) or (isinstance(c, (cfg.Value, cfg.Remove)) and c.key == key):
            return c
    return None


def _own_defines(node: cfg.Struct, keys: list[str]) -> bool:
    """Whether node itself sets the field at keys, removes it, or cuts it off from its parent with {bskipref}. A node
    that defines a list owns all of it, so an item its parent adds at a new index is not inherited."""
    if 'bskipref' in node.flags:
        return True
    for depth, key in enumerate(keys):
        found = _child(node, key)
        if found is None:
            return False
        if (depth == len(keys) - 1 or not isinstance(found, cfg.Struct) or 'bskipref' in found.flags
                or _is_index(keys[depth + 1])):
            return True
        node = found
    return False


def _patched_paths(parsed: list[tuple[str, Target, list, str | None]]) -> dict[Target, dict[str, set[str]]]:
    out: dict[Target, dict[str, set[str]]] = {}
    for _, target, roots, dlc in parsed:
        if dlc is None:
            for node in roots:
                if isinstance(node, cfg.Struct) and node.bpatch:
                    out.setdefault(target, {}).setdefault(node.name, set()).update(_set_paths(node.children))
    return out


def _covers(paths: set[str], path: str) -> bool:
    return any(p == path or path.startswith(f'{p}.') or p.startswith(f'{path}.') for p in paths)


INHERITORS_SHOWN = 5


def _inheritance_findings(roots: list, target: Target, vanilla: Vanilla, patched: dict[str, set[str]],
                          file: str) -> list[Finding]:
    # In game, a patch to a technician's Upgrades list did not reach Screw, who inherits it (2026-11-09), and a
    # RecoilParams patch on GunAK74_ST did not reach Gun_Combatant_AR_GS (2026-11-15). Both were binarized tables.
    # Other tables and plain cfg are untested, hence "may not".
    findings: list[Finding] = []
    for node in roots:
        if not (isinstance(node, cfg.Struct) and node.bpatch):
            continue
        paths = {path: path.split('.') for path in _set_paths(node.children)}
        missed: dict[str, None] = {}
        missed_paths: set[str] = set()
        seen: set[int] = set()
        for entry in vanilla.lookup_all(target, node.name):
            stack = [(child, [child.node]) for child in vanilla.children_of(entry)]
            while stack:
                child, chain = stack.pop()
                if id(child.node) in seen:
                    continue
                seen.add(id(child.node))
                for path, keys in paths.items():
                    if (not any(_own_defines(n, keys) for n in chain)
                            and not _covers(patched.get(child.node.name, set()), path)):
                        missed[child.node.name] = None
                        missed_paths.add(path)
                stack.extend((grandchild, chain + [grandchild.node]) for grandchild in vanilla.children_of(child))
        if missed:
            names = sorted(missed)
            shown = ', '.join(names[:INHERITORS_SHOWN]) + (f' and {len(names) - INHERITORS_SHOWN} more'
                                                           if len(names) > INHERITORS_SHOWN else '')
            fields = sorted(missed_paths)
            field_text = ', '.join(fields[:3]) + (f' and {len(fields) - 3} more' if len(fields) > 3 else '')
            findings.append(Finding('warning', file, node.line,
                                    f'{len(names)} SID(s) inherit {field_text} from {node.name} through refkey and '
                                    f'may not get this patch: {shown}. Patch them too if they should change',
                                    f'patches to {field_text} in {target.table} that SIDs inheriting through refkey '
                                    'may not get', node.name))
    return findings


def _sorts_after(name: str, other: str) -> bool:
    # In game 2026-11-10, the patch file whose name sorts later won. Whether that sort ignores case is untested, so
    # only a name that sorts later both ways is safe.
    return name > other and name.casefold() > other.casefold()


def _order_findings(main: list[tuple[str, Target, list, str | None]],
                    option: list[tuple[str, Target, list, str | None]]) -> list[Finding]:
    # The sort-order rule was measured on binarized tables only, so plain-cfg patches are not checked.
    findings: list[Finding] = []
    main_files = [(PurePosixPath(file), _set_paths(roots)) for file, target, roots, _ in main
                  if target.kind == 'binarized']
    for file, target, roots, _ in option:
        if target.kind != 'binarized':
            continue
        path, paths = PurePosixPath(file), _set_paths(roots)
        for main_path, main_paths in main_files:
            # build._same_game_paths reports a file at the same path.
            if (main_path.parent != path.parent or main_path.name.casefold() == path.name.casefold()
                    or _sorts_after(path.name, main_path.name)):
                continue
            hit = _overlap(paths, main_paths)
            if hit:
                findings.append(Finding('warning', file, hit[1],
                                        f"{hit[0]} is also set by the main part's {main_path.name}. The game uses the "
                                        "patch file whose name sorts last, so the main part's value wins. Give this "
                                        f'file a name that sorts after {main_path.name}'))
    return findings


def check_parts(cfg_roots: list[Path], tables: Tables, vanilla: Vanilla,
                dlc_tables: dict[str, Tables] | None = None) -> list[list[Finding]]:
    """cfg_roots[0] is the main part's cfg/ and the rest are the options'. Returns each part's findings, with paths
    relative to its own cfg/. dlc_tables maps each DLC folder name under cfg/DLCGameData/ to that DLC's tables."""
    dlc_tables = dlc_tables or {}
    results: list[list[Finding]] = []
    main_sids: dict[Target, set[str]] = {}
    main_patched: dict[Target, dict[str, set[str]]] = {}
    main_parsed: list[tuple[str, Target, list, str | None]] = []
    for number, cfg_root in enumerate(cfg_roots):
        findings, parsed = _scan(cfg_root, tables, dlc_tables)
        defined = _new_sids(parsed)
        patched = _patched_paths(parsed)
        if number == 0:
            main_sids, main_patched, main_parsed = defined, patched, parsed
        else:
            findings.extend(_order_findings(main_parsed, parsed))
            # The main part is always installed, so an option's refkey can name its new structs. Options install in
            # any combination, so one option's new structs do not count for another, or for the main part.
            defined = {target: sids | main_sids.get(target, set()) for target, sids in defined.items()}
            for target, by_sid in main_patched.items():
                for sid, paths in by_sid.items():
                    patched.setdefault(target, {}).setdefault(sid, set()).update(paths)
        for file, target, roots, dlc in parsed:
            _check_unknown(roots, file, findings)
            if dlc:
                _check_dlc_file(roots, dlc, file, findings)
            else:
                _check_file(roots, target, vanilla, file, defined[target], findings)
                if target.kind == 'binarized':
                    findings.extend(_inheritance_findings(roots, target, vanilla, patched.get(target, {}), file))
        results.append(findings)
    return results


def check_project(cfg_root: Path, tables: Tables, vanilla: Vanilla,
                  dlc_tables: dict[str, Tables] | None = None) -> list[Finding]:
    """Checks one part with no other parts installed."""
    return check_parts([cfg_root], tables, vanilla, dlc_tables)[0]
