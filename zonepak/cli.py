"""Command line: zonepak new | check | build | tables | text."""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from . import build, fetch, zonekit
from .check import Finding, summarize
from .locdb import CULTURES
from .project import KIT_LEVELS, ProjectError, load_config, load_project, new_project
from .tables import describe
from .tools import ToolError


def _write_log(project, findings: list[Finding]) -> Path:
    log = project.build_dir / 'check.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(''.join(f'{f}\n' for f in findings), encoding='utf-8')
    return log


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='zonepak', description='Build S.T.A.L.K.E.R. 2 mods into Zone Kit layouts.')
    parser.add_argument('--project', type=Path, default=Path.cwd(), help='project folder (default: current folder)')
    parser.add_argument('--config', type=Path, help='user config file')
    parser.add_argument('--zone-kit', type=Path, help='Zone Kit install folder')
    parser.add_argument('--zone-kit-mode', choices=KIT_LEVELS,
                        help='work as if only this Zone Kit level were installed (default: the level detected)')
    parser.add_argument('--game', type=Path, help='game install folder')
    parser.add_argument('--repak', type=Path, help='repak.exe')
    parser.add_argument('--retoc', type=Path, help='the patched retoc.exe from STALKER2-zonekit-retoc')
    sub = parser.add_subparsers(dest='command', required=True)
    new = sub.add_parser('new', help='create a project folder inside --project')
    new.add_argument('name')
    sub.add_parser('check', help='validate patch files against the vanilla tables, and text files')
    sub.add_parser('build', help='check, then write build/')
    tables = sub.add_parser('tables', help='list the binarized tables and plain cfg files a patch can target')
    tables.add_argument('--dlc', metavar='NAME', help=r'list the tables of the DLC in <game>\NAME\ instead')
    text = sub.add_parser('text', help="find the game's text keys by key or by text, printed as text file lines")
    text.add_argument('query', help='part of a key or of its text, any case')
    text.add_argument('--culture', default='en', choices=CULTURES, help='culture to search and print (default: en)')
    text.add_argument('--limit', type=int, default=50, help='most lines to print, 0 for all (default: 50)')
    return parser


def _toml_line(key: str, text: str) -> str:
    def quote(s: str) -> str:
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        escaped = ''.join(c if c >= ' ' or c == '\t' else f'\\u{ord(c):04x}' for c in escaped)
        return f'"{escaped}"'
    bare = key and all(c.isascii() and (c.isalnum() or c in '_-') for c in key)
    return f'{key if bare else quote(key)} = {quote(text)}'


def search_text(texts: dict[str, str], query: str) -> list[str]:
    needle = query.lower()
    return [_toml_line(key, text) for key, text in sorted(texts.items())
            if needle in key.lower() or needle in text.lower()]


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == 'new':
            print(f'created {new_project(args.project, args.name)}')
            return 0
        overrides = {'zone_kit': args.zone_kit, 'zone_kit_mode': args.zone_kit_mode, 'game': args.game,
                     'repak': args.repak, 'retoc': args.retoc}
        config = dataclasses.replace(load_config(args.config, overrides), cli=True)
        if args.command == 'tables':
            if args.dlc:
                lines = describe(build.game_dlc_tables(config, args.dlc), f'cfg/DLCGameData/{args.dlc}')
            else:
                lines = describe(build.game_tables(config))
            print('\n'.join(lines))
            return 0
        if args.command == 'text':
            # Redirected output would otherwise use the ANSI code page, which cannot encode most cultures' text,
            # and text files must be UTF-8 anyway.
            sys.stdout.reconfigure(encoding='utf-8')
            lines = search_text(build.game_text(config).culture(args.culture), args.query)
            shown = lines if args.limit <= 0 else lines[:args.limit]
            if shown:
                print('\n'.join(shown))
            print(f'{len(lines)} match(es)' + (f', first {len(shown)} shown. Use --limit 0 for all'
                                                if len(shown) < len(lines) else ''))
            return 0
        project = load_project(args.project)
        print(zonekit.report(config))
        findings = build.run_check(project, config)
        lines = summarize(findings)
        for line in lines:
            print(line)
        log = _write_log(project, findings)
        if args.command == 'check':
            errors = sum(f.level == 'error' for f in findings)
            print(f'{errors} error(s), {len(findings) - errors} warning(s)'
                  + (f'. Every finding is in {log}' if len(lines) < len(findings) else ''))
            return 1 if errors else 0
        print(f'built {build.build(project, config, findings=findings, report=print)}')
        # build replaces the whole build folder.
        _write_log(project, findings)
        return 0
    except (build.BuildError, fetch.FetchError, ProjectError, ToolError, ValueError, OSError) as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('interrupted', file=sys.stderr)
        return 130
