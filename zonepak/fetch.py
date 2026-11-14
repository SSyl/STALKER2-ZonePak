"""Downloads repak and the patched retoc into third_party/ when the config names neither."""
from __future__ import annotations

import hashlib
import http.client
import io
import sys
import urllib.request
import webbrowser
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

THIRD_PARTY = Path(__file__).resolve().parent.parent / 'third_party'


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Download:
    exe: str
    page: str
    url: str
    sha256: str


# Each sha256 pins one published release asset. Release a retoc change under a new tag and leave old releases up:
# rebuilt assets get a new hash, and copies of ZonePak already downloaded keep checking for the old one.
DOWNLOADS = {
    'repak': Download(
        'repak.exe',
        'https://github.com/trumank/repak/releases/tag/v0.2.3',
        'https://github.com/trumank/repak/releases/download/v0.2.3/repak_cli-x86_64-pc-windows-msvc.zip',
        '6720d602144d75df477a99d5bedb6ea780997546afc335901d4937cafeaa73fa'),
    'retoc': Download(
        'retoc.exe',
        'https://github.com/SSyl/STALKER2-zonekit-retoc/releases/tag/v0.1.5-zonekit.1',
        'https://github.com/SSyl/STALKER2-zonekit-retoc/releases/download/v0.1.5-zonekit.1/'
        'retoc_cli-x86_64-pc-windows-msvc.zip',
        '1a54564dce1d70f6a202f63242ad1a8a066edd46a1eb7eeea2e49ef579d9d6fb'),
}


def local_path(key: str) -> Path:
    return THIRD_PARTY / DOWNLOADS[key].exe


def manual_steps(key: str, cli: bool = False) -> str:
    d = DOWNLOADS[key]
    return (f'Download {d.url.rsplit("/", 1)[1]} from {d.page}, extract {d.exe} from it into {THIRD_PARTY}, and '
            f'run the command again. Or set {key} in the config file' + (f', or pass --{key}.' if cli else '.'))


def ensure(key: str, ask: Callable[[str], str] = input, open_page: Callable[[str], object] = webbrowser.open,
           interactive: bool | None = None, fetch: Callable[[str], bytes] | None = None, cli: bool = False) -> Path:
    """The tool's path in third_party/, downloading it there after the user agrees."""
    dest = local_path(key)
    if dest.is_file():
        return dest
    d = DOWNLOADS[key]
    if interactive is None:
        interactive = sys.stdin.isatty()
    unanswerable = FetchError(f'{key} is not set and {dest} does not exist. {manual_steps(key, cli)}')
    if not interactive:
        raise unanswerable
    question = f'{key} is not set and {dest} does not exist. Download {d.exe} from {d.page}? [y/n] '
    try:
        while (answer := ask(question).strip().lower()) not in ('y', 'n'):
            pass
    except EOFError:
        raise unanswerable from None
    if answer == 'n':
        open_page(d.page)
        raise FetchError(manual_steps(key, cli))
    data = (fetch or _get)(d.url)
    digest = hashlib.sha256(data).hexdigest()
    if digest != d.sha256:
        raise FetchError(f'{d.url} has SHA-256 {digest}, expected {d.sha256}. Nothing was written.')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        exe = z.read(d.exe)
    THIRD_PARTY.mkdir(exist_ok=True)
    partial = dest.with_suffix('.part')
    partial.write_bytes(exe)
    partial.replace(dest)
    print(f'downloaded {dest}')
    return dest


def _get(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            return response.read()
    except (OSError, http.client.HTTPException) as e:
        raise FetchError(f'cannot download {url}: {e}') from e
