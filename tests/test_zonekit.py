import tempfile
import unittest
from pathlib import Path

from zonepak import build, zonekit
from zonepak.project import Config, ProjectError, load_config, load_project, new_project
from tests.test_build import PATCH_A


class ZoneKitLevelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kit = Path(self.tmp.name) / 'kit'
        (self.kit / zonekit.GAME_DATA).mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def install_editor(self):
        for rel in zonekit.FULL_EDITOR:
            (self.kit / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.kit / rel).write_bytes(b'')

    def test_detects_each_install(self):
        self.assertEqual(zonekit.level(Config()), 'none')
        self.assertEqual(zonekit.level(Config(zone_kit=self.kit)), 'lesser')
        self.install_editor()
        self.assertEqual(zonekit.level(Config(zone_kit=self.kit)), 'full')
        with self.assertRaisesRegex(ProjectError, 'Is zone_kit set to the Zone Kit install folder'):
            zonekit.level(Config(zone_kit=Path(self.tmp.name) / 'NotTheKit'))

    def test_mode_lowers_but_never_raises_the_level(self):
        self.install_editor()
        self.assertEqual(zonekit.level(Config(zone_kit=self.kit, zone_kit_mode='lesser')), 'lesser')
        self.assertEqual(zonekit.level(Config(zone_kit=Path(self.tmp.name) / 'NotTheKit', zone_kit_mode='none')),
                         'none')
        (self.kit / zonekit.FULL_EDITOR[1]).unlink()
        with self.assertRaisesRegex(ProjectError, r'zone_kit_mode = full, but .* is the lesser Zone Kit'):
            zonekit.level(Config(zone_kit=self.kit, zone_kit_mode='full'))
        with self.assertRaisesRegex(ProjectError, r'zone_kit_mode = lesser, but zone_kit is not set'):
            zonekit.level(Config(zone_kit_mode='lesser'))

    def test_config_file_mode_must_be_a_level(self):
        path = Path(self.tmp.name) / 'config.toml'
        path.write_text("zone_kit_mode = 'lesser'\n", encoding='utf-8')
        self.assertEqual(load_config(path).zone_kit_mode, 'lesser')
        path.write_text("zone_kit_mode = 'Full'\n", encoding='utf-8')
        with self.assertRaisesRegex(ProjectError, r'zone_kit_mode must be one of none, lesser, full$'):
            load_config(path)

    def test_mode_none_keeps_cfg_checks_off_the_kit(self):
        root = new_project(Path(self.tmp.name), 'ZpTest', now=lambda: 1700000000)
        (root / 'cfg/GameData/ItemPrototypes').mkdir(parents=True)
        (root / 'cfg/GameData/ItemPrototypes/ZpTest.cfg').write_text(PATCH_A, encoding='utf-8')
        with self.assertRaisesRegex(ProjectError, r'Checking cfg patches needs the lesser Zone Kit or higher, and '
                                                  r'zone_kit_mode = none keeps ZonePak from using'):
            build.run_check(load_project(root), Config(zone_kit=self.kit, zone_kit_mode='none'))
