"""Runs repak and retoc."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


class ToolError(RuntimeError):
    pass


def _run(cmd: list, env: dict | None = None) -> str:
    try:
        result = subprocess.run([str(c) for c in cmd], capture_output=True, encoding='utf-8', errors='replace',
                                env=env)
    except OSError as e:
        raise ToolError(f'cannot run {cmd[0]}: {e}') from e
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ToolError(f'{Path(str(cmd[0])).name} {cmd[1]} failed ({result.returncode}): {detail}')
    return result.stdout


def pak_get(repak: Path, pak: Path, entry: str) -> bytes:
    """One file from a pak, by its path below the mount point."""
    try:
        result = subprocess.run([str(repak), 'get', str(pak), entry], capture_output=True)
    except OSError as e:
        raise ToolError(f'cannot run {repak}: {e}') from e
    if result.returncode != 0:
        detail = result.stderr.decode('utf-8', 'replace').strip()
        raise ToolError(f'{Path(str(repak)).name} get failed ({result.returncode}): {detail}')
    return result.stdout


def pak_list(repak: Path, pak: Path) -> list[str]:
    return [line for line in _run([repak, 'list', pak]).splitlines() if line.strip()]


def pak_pack(repak: Path, src_dir: Path, mount_point: str, out_pak: Path) -> None:
    _run([repak, 'pack', '-q', '--version', 'V11', '--mount-point', mount_point, src_dir, out_pak])


def pak_unpack(repak: Path, pak: Path, out_dir: Path) -> None:
    _run([repak, 'unpack', '-q', '-f', '-o', out_dir, pak])


def pak_mount_point(repak: Path, pak: Path) -> str:
    for line in _run([repak, 'info', pak]).splitlines():
        if line.startswith('mount point:'):
            return line.split(':', 1)[1].strip()
    raise ToolError(f'repak info printed no mount point for {pak}')


def to_zen(retoc: Path, legacy_dir: Path, out_utoc: Path, mount_point: str, redirects: dict[str, str]) -> None:
    """Needs the patched retoc from STALKER2-zonekit-retoc, which reads both environment variables."""
    env = dict(os.environ, RETOC_TOC_MOUNT_POINT=mount_point,
               RETOC_PACKAGE_REDIRECTS=';'.join(f'{s}={t}' for s, t in redirects.items()))
    _run([retoc, 'to-zen', '--version', 'UE5_5', legacy_dir, out_utoc], env=env)


def retoc_list(retoc: Path, utoc: Path) -> list[str]:
    return [line for line in _run([retoc, 'list', utoc]).splitlines() if line.strip()]
