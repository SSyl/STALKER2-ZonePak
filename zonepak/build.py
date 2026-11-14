"""check and build: staging, output folders and file names."""
from __future__ import annotations

import hashlib
import json
import posixpath
import shutil
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Callable

from . import __version__, check, fomod, locdb, locres, tools, uasset
from .check import Finding
from .project import Config, Project, ProjectError
from .tables import DLC_GAME_DATA, PLAIN_PATCH, Tables
from .vanilla import Vanilla

GAME_LITE = 'Stalker2/Content/GameLite/'
PAKCHUNK0 = 'Stalker2/Content/Paks/pakchunk0-Windows.pak'
KIT_GAME_DATA = 'Stalker2/Content/GameLite/GameData'


class BuildError(RuntimeError):
    def __init__(self, message: str, findings: list[Finding] | None = None):
        super().__init__(message)
        self.findings = list(findings or [])


def run_check(project: Project, config: Config) -> list[Finding]:
    cfg_dirs = [project.cfg_dir] + [option.cfg_dir for option in project.options]
    if any(_has_files(cfg_dir) for cfg_dir in cfg_dirs):
        findings, *option_findings = _check_cfg(cfg_dirs, config)
    else:
        findings, option_findings = [], [[] for _ in project.options]
    try:
        entries = locdb.load_text(project.text_dir)
    except locdb.TextError as e:
        entries = {}
        findings.append(Finding('error', f'text/{e.file}', 0, e.message))
    findings += _text_findings(project, entries, config)
    for option, found in zip(project.options, option_findings):
        prefix = _option_cfg(project, option) + '/'
        findings += [replace(f, file=prefix + f.file) for f in found]
        has_patches = bool(_patch_files(option.cfg_dir))
        if option.empty and has_patches:
            findings.append(Finding('error', _option_cfg(project, option), 0,
                                    'the option has empty = true, so build leaves out its patch files. Remove '
                                    'empty = true, or the files'))
        elif not option.empty and not has_patches:
            findings.append(Finding('error', _option_cfg(project, option), 0,
                                    f'no patch files under {prefix}GameData/ or {prefix}DLCGameData/<DLC>/, so the '
                                    'option installs nothing. Add empty = true if that is intended'))
    return findings + _same_game_paths(project)


def _has_files(cfg_dir: Path) -> bool:
    return cfg_dir.is_dir() and any(p.is_file() and not check.is_os_file(p) for p in cfg_dir.rglob('*'))


def _check_cfg(cfg_dirs: list[Path], config: Config) -> list[list[Finding]]:
    game_data = config.require('zone_kit') / KIT_GAME_DATA
    if not game_data.is_dir():
        raise ProjectError(f'{game_data} not found. Is zone_kit set to the Zone Kit install folder?')
    tables = game_tables(config)
    dlcs = sorted({dlc for cfg_dir in cfg_dirs for dlc in _dlc_names(cfg_dir)})
    dlc_tables = {dlc: game_dlc_tables(config, dlc) for dlc in dlcs}
    return check.check_parts(cfg_dirs, tables, Vanilla(game_data, tables), dlc_tables)


def game_dir(config: Config) -> Path:
    game = config.require('game')
    if not (game / PAKCHUNK0).is_file():
        raise ProjectError(f'{game / PAKCHUNK0} not found. Is game set to the folder that holds Stalker2.exe?')
    return game


def game_text(config: Config) -> locres.GameText:
    return locres.GameText(config.require('repak'), game_dir(config))


def _text_findings(project: Project, entries: dict[str, dict[str, str]], config: Config) -> list[Finding]:
    if not entries:
        return []
    game_keys = game_text(config).culture('en')
    findings = []
    for key, missing in sorted(locdb.gaps(entries, game_keys, project.copy_new_text).items()):
        given = next(c for c in locdb.CULTURES if c in entries[key])
        cultures = f'{len(missing)} culture(s) ({", ".join(missing)})'
        message = (f"{key} is not one of the game's text keys and has no text for {cultures}, so players using "
                   'those languages see the raw key. If it is a new key, add their texts or set copy_new_text = '
                   f'"{given}" in zonepak.toml. If not, check its spelling with "zonepak text"')
        findings.append(Finding('warning', f'text/{given}.toml', 0, message))
    return findings


def _option_cfg(project: Project, option) -> str:
    """The option's cfg/ folder as findings name it, relative to the project."""
    return (option.cfg_dir).relative_to(project.root).as_posix()


def _same_game_paths(project: Project) -> list[Finding]:
    findings: list[Finding] = []
    first: dict[str, str] = {}
    parts = [('', project.cfg_dir)] + [(_option_cfg(project, option) + '/', option.cfg_dir) for option in project.options]
    for prefix, cfg_dir in parts:
        for rel, _ in _patch_files(cfg_dir):
            file = prefix + rel
            other = first.setdefault(rel.lower(), file)
            if other != file:
                findings.append(Finding('warning', file, 0,
                                        f'has the same game path as {other}, so the game loads only one of them'))
    return findings


def game_tables(config: Config) -> Tables:
    return Tables.from_pak_listing(tools.pak_list(config.require('repak'), game_dir(config) / PAKCHUNK0))


def game_dlc_tables(config: Config, dlc: str) -> Tables:
    repak, game = config.require('repak'), game_dir(config)
    # Windows paths ignore case but pak entries do not, so `dlc1` would find the pak and then match no table.
    same = [p.name for p in game.iterdir() if p.is_dir() and p.name.lower() == dlc.lower()] if game.is_dir() else []
    if same and dlc not in same:
        raise ProjectError(f"DLC folder '{dlc}' must be spelled {same[0]}, like the game folder")
    prefix = f'{DLC_GAME_DATA}{dlc}/'
    paks = sorted((game / dlc).glob('*.pak'))
    if paks:
        entries = [entry for pak in paks for entry in tools.pak_list(repak, pak)]
        return Tables.from_pak_listing(entries, prefix)
    # Deluxe, Ultimate and PreOrder data ship inside the main game paks (pakchunk101, 102 and 104) under
    # DLCGameData/<name>/, with no folder of their own in the game install.
    main_paks = sorted((game / PAKCHUNK0).parent.glob('pakchunk*-Windows.pak'))
    entries = [entry for pak in main_paks for entry in tools.pak_list(repak, pak) if entry.startswith(prefix)]
    if not entries:
        raise ProjectError(f'{dlc} is not a DLC folder in the game install (no {game / dlc / "*.pak"}) and no main '
                           f'game pak has {prefix} (the name is case-sensitive, as in Deluxe)')
    return Tables.from_pak_listing(entries, prefix)


def _dlc_names(cfg_dir: Path) -> list[str]:
    root = cfg_dir / 'DLCGameData'
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def _patch_files(cfg_dir: Path) -> list[tuple[str, Path]]:
    roots = [cfg_dir / 'GameData'] + [cfg_dir / 'DLCGameData' / dlc for dlc in _dlc_names(cfg_dir)]
    return [(p.relative_to(cfg_dir).as_posix(), p) for root in roots if root.is_dir()
            for p in sorted(root.rglob('*')) if p.is_file() and (p.suffix == '.cfg' or PLAIN_PATCH.match(p.name))]


def _copy_patches(patches: list[tuple[str, Path]], stage: Path) -> None:
    for rel, src in patches:
        dst = stage / GAME_LITE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def _pack_cfg_only(repak: Path, patches: list[tuple[str, Path]], stage: Path, out_pak: Path) -> None:
    """Packs what _copy_patches staged, mounted at the deepest folder the patches share, as PakPlainMod.bat does."""
    common = posixpath.commonpath([posixpath.dirname(GAME_LITE + rel) for rel, _ in patches])
    tools.pak_pack(repak, stage / common, f'../../../{common}/', out_pak)


def build(project: Project, config: Config, findings: list[Finding] | None = None,
          report: Callable[[str], None] | None = None) -> Path:
    if findings is None:
        findings = run_check(project, config)
    errors = [f for f in findings if f.level == 'error']
    if errors:
        raise BuildError(f'{len(errors)} error(s) in patch or text files', findings)
    patches = _patch_files(project.cfg_dir)
    entries = locdb.load_text(project.text_dir)
    if not patches and not entries:
        raise BuildError('nothing to build: no patch files under cfg/GameData/ or cfg/DLCGameData/ and no text/*.toml '
                         'entries' + ('. Options cannot be the whole mod, so the main part needs patches or text too'
                                      if project.options else ''))

    final = project.build_dir
    out, old = final.with_name(final.name + '.partial'), final.with_name(final.name + '.old')
    for leftover in (out, old):
        shutil.rmtree(leftover, ignore_errors=True)
    try:
        _write_build(project, config, patches, entries, out, report)
        if final.exists():
            try:
                final.rename(old)
            except OSError as e:
                raise BuildError(f'cannot replace {final}: {e}. Close any program that has a file in it open, and '
                                 'build again.') from e
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    try:
        out.rename(final)
    except OSError:
        if old.exists():
            old.rename(final)
        raise
    shutil.rmtree(old, ignore_errors=True)
    return final / project.name


def _write_build(project: Project, config: Config, patches: list[tuple[str, Path]], entries: dict[str, dict[str, str]],
                 out: Path, report: Callable[[str], None] | None) -> None:
    name = project.name
    base = f'{name}Stalker2-Windows'
    stage = out / 'stage'
    flat = out / name
    flat.mkdir(parents=True)
    loose = stage / 'pak' / GAME_LITE
    loose.mkdir(parents=True)
    _copy_patches(patches, stage / 'pak')
    info: dict = {'zonepak': __version__, 'name': name, 'version': project.version}
    info.update({key: value for key, value in (('author', project.author), ('website', project.website),
                                               ('nexus_id', project.nexus_id)) if value})

    if entries:
        entries, from_game, copied = locdb.fill_cultures(entries, game_text(config).culture,
                                                         project.fill_game_text, project.copy_new_text)
        if report and (from_game or copied):
            report(f'text: {from_game} text(s) taken from the game for cultures the text files leave out'
                   + (f', {copied} copied from {project.copy_new_text}' if copied else ''))
        stem, header, body = uasset.build_locdb_package(name, project.database_id, locdb.export_body(entries))
        legacy = stage / 'legacy' / 'Stalker2' / 'Content'
        legacy.mkdir(parents=True)
        (legacy / f'{stem}.uasset').write_bytes(header)
        (legacy / f'{stem}.uexp').write_bytes(body)
        zen = stage / 'zen'
        zen.mkdir()
        # The container id is hashed from the file stem, so convert under the Zone Kit's base name and rename.
        tools.to_zen(config.require('retoc'), stage / 'legacy', zen / f'{base}.utoc', '../../../Stalker2/Content/',
                     {f'/Game/{stem}': f'/{name}/{stem}'})
        if f'/Game/{stem}'.encode() not in (zen / f'{base}.ucas').read_bytes():
            raise BuildError('retoc wrote no package redirect. Set retoc to the patched build from STALKER2-zonekit-retoc.')
        for ext in ('utoc', 'ucas'):
            shutil.copyfile(zen / f'{base}.{ext}', flat / f'{base}-OverrideContent.{ext}')
        tools.pak_pack(config.require('repak'), loose, '../../../' + GAME_LITE, flat / f'{base}-OverrideContent.pak')
        info['database'] = stem
    else:
        _pack_cfg_only(config.require('repak'), patches, stage / 'pak', flat / f'{base}-OverrideContent.pak')

    # @todo Plugin mods (a NewContent part with GameFeatureData) also need AssetRegistry.bin, whose FName batch
    # needs CityHash64. Neither exists yet. See README Todo.
    # The zip's main part is taken before the default options' paks join build/<Name>/.
    main_files = sorted(flat.iterdir())

    option_paks = []
    for option in project.options:
        if option.empty:
            continue
        option_patches = _patch_files(option.cfg_dir)
        option_stage = stage / 'options' / option.folder
        _copy_patches(option_patches, option_stage)
        pak = stage / 'option-paks' / option.folder / f'{name}_{option.folder}Stalker2-Windows-OverrideContent.pak'
        pak.parent.mkdir(parents=True)
        _pack_cfg_only(config.require('repak'), option_patches, option_stage, pak)
        option_paks.append((option, pak))
        if option.default:
            shutil.copyfile(pak, flat / pak.name)

    with zipfile.ZipFile(out / f'{name}-{project.version}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        if not project.options:
            for f in main_files:
                z.write(f, f'{name}/{f.name}')
        else:
            z.writestr('fomod/info.xml', fomod.info_xml(project))
            z.writestr('fomod/ModuleConfig.xml', fomod.module_config_xml(project))
            for image in dict.fromkeys(option.image for option in project.options if option.image):
                z.write(image, f'{fomod.IMAGES}/{image.name}')
            for f in main_files:
                z.write(f, f'{fomod.MAIN_FOLDER}/{f.name}')
            for option, pak in option_paks:
                z.write(pak, f'{option.folder}/{pak.name}')
    info['files'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(flat.iterdir())}
    (out / 'build.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    shutil.rmtree(stage)

