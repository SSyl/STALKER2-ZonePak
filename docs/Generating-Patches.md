# Generating patches from a script

This page shows how to have a script write the patch files and then build the mod.

For data-driven mods, have a script write the patch files into `cfg/GameData/` (and text into `text/`), then run
`check` and `build`. In this example, `zonepak_folder` is the ZonePak folder from step 0 of the README's quick
start and `project` is the mod's project folder:

```python
import subprocess
import sys
from pathlib import Path

zonepak_folder = r'C:\Tools\ZonePak'
project = Path(r'C:\Mods\MyMod')
patch = project / 'cfg' / 'GameData' / 'ItemPrototypes' / 'MyMod.cfg'
patch.parent.mkdir(parents=True, exist_ok=True)
patch.write_text(''.join(
    f'{sid} : struct.begin {{bpatch}}\r\n   Magazine : struct.begin {{bpatch}}\r\n      MaxAmmo = {n}\r\n'
    '   struct.end\r\nstruct.end\r\n' for sid, n in [('GunPM_MagDefault', 10)]), encoding='utf-8', newline='')
subprocess.run([sys.executable, '-m', 'zonepak', '--project', str(project), 'build'],
               cwd=zonepak_folder, check=True)
```

- `check` and `build` exit with 1 when there are errors, so `check=True` stops the script.
- `build` packs every `.cfg` and `.cfg_patch_*` file under `cfg/GameData/` and `cfg/DLCGameData/<DLC>/`, so delete
  files the script no longer generates.
- Keep the script's own data outside `cfg/`, because `check` warns about every other file in there.
- Files are copied byte for byte. The game's own files use CRLF line endings.
