import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from zonepak import build, tools
from zonepak.project import Config, load_project, new_project

KIT = os.environ.get('ZONEPAK_TEST_ZONE_KIT')
REPAK = os.environ.get('ZONEPAK_TEST_REPAK')
NAME = 'ZonePakParity'
KIT_FOLDERS = ('Stalker2/Mods', 'Stalker2/SavedMods', 'Stalker2/SavedMods/Staged', 'Stalker2/SavedMods/Cooked')
FILES = {
    'GameData/ItemPrototypes/zzz_ZonePakParity.cfg': 'GunUDP_MagDefault : struct.begin {bpatch}\r\nstruct.end\r\n',
    'GameData/UpgradePrototypes/zzz_ZonePakParity.cfg': 'GunUDP_Upgrade_Barrel_1 : struct.begin {bpatch}\r\nstruct.end\r\n',
    'GameData/CoreVariables.cfg_patch_ZonePakParity': 'DefaultConfig : struct.begin {bpatch}\r\nstruct.end\r\n',
}


@unittest.skipUnless(KIT and REPAK, 'ZONEPAK_TEST_ZONE_KIT and ZONEPAK_TEST_REPAK not set')
class OfficialParityTest(unittest.TestCase):
    def setUp(self):
        self.kit = Path(KIT)
        self.repak = Path(REPAK)
        self.created = [self.kit / rel for rel in KIT_FOLDERS if not (self.kit / rel).exists()]
        self.tmp = tempfile.TemporaryDirectory()
        self.cleanup_kit()

    def tearDown(self):
        try:
            self.cleanup_kit()
            # A folder that is not empty after cleanup_kit holds files the test did not make, so rmdir must fail on it.
            for folder in sorted(self.created, key=lambda p: len(p.parts), reverse=True):
                if folder.exists():
                    os.rmdir(folder)
        finally:
            self.tmp.cleanup()

    def cleanup_kit(self):
        for rel in (f'Stalker2/Mods/{NAME}', f'Stalker2/SavedMods/Staged/{NAME}', f'Stalker2/SavedMods/Cooked/{NAME}'):
            shutil.rmtree(self.kit / rel, ignore_errors=True)

    def run_bat(self, bat):
        result = subprocess.run([str(self.kit / bat), NAME], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:])

    def unpack(self, pak, name):
        out = Path(self.tmp.name) / name
        tools.pak_unpack(self.repak, pak, out)
        return {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()}

    def test_cfg_only_output_matches_pakplainmod(self):
        root = new_project(Path(self.tmp.name), NAME, now=lambda: 1700000000)
        for rel, text in FILES.items():
            (root / 'cfg' / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / 'cfg' / rel).write_bytes(text.encode())
        ours = build.build(load_project(root), Config(repak=self.repak), findings=[]) / \
            f'{NAME}Stalker2-Windows-OverrideContent.pak'

        self.run_bat('CreatePlainMod.bat')
        for rel, text in FILES.items():
            dst = self.kit / f'Stalker2/Mods/{NAME}/Content/GameLite' / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(text.encode())
        self.run_bat('PakPlainMod.bat')
        staged = self.kit / f'Stalker2/SavedMods/Staged/{NAME}/Windows/OverrideContent/Windows'
        theirs = staged / f'Stalker2/Mods/{NAME}/Content/Paks/Windows/{NAME}Stalker2-Windows-OverrideContent.pak'

        self.assertEqual(self.unpack(ours, 'ours'), self.unpack(theirs, 'theirs'))
        self.assertEqual(tools.pak_mount_point(self.repak, ours), tools.pak_mount_point(self.repak, theirs))


if __name__ == '__main__':
    unittest.main()
