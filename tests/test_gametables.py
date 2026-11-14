import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zonepak import build, cfg, gametables
from zonepak.project import Config

REPAK = os.environ.get('ZONEPAK_TEST_REPAK')
GAME = os.environ.get('ZONEPAK_TEST_GAME')
ZONE_KIT = os.environ.get('ZONEPAK_TEST_ZONE_KIT')


class FakeGameTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        game = Path(self.tmp.name) / 'game'
        (game / build.PAKCHUNK0).parent.mkdir(parents=True)
        (game / build.PAKCHUNK0).write_bytes(b'')
        self.config = Config(game=game, repak=Path('repak.exe'))
        gametables._listing.cache_clear()
        self.addCleanup(gametables._listing.cache_clear)

    def test_part_not_installed_is_none(self):
        with mock.patch('zonepak.tools.pak_list', side_effect=AssertionError('listed')):
            self.assertIsNone(gametables.table_text(self.config, 'DLC1', 'ItemPrototypes'))
            self.assertEqual(gametables.table(self.config, 'DLC1', 'ItemPrototypes'), [])

    def test_table_missing_from_the_pak_is_none(self):
        with mock.patch('zonepak.tools.pak_list', return_value=[]), \
                mock.patch('zonepak.tools.pak_get', side_effect=AssertionError('read')):
            self.assertIsNone(gametables.table_text(self.config, 'base', 'ItemPrototypes'))


@unittest.skipUnless(REPAK and GAME, 'ZONEPAK_TEST_REPAK and ZONEPAK_TEST_GAME not set')
class RealGameTest(unittest.TestCase):
    def test_decodes_a_base_table(self):
        config = Config(game=Path(GAME), repak=Path(REPAK))
        sids = {n.name for n in gametables.table(config, 'base', 'WeaponData/CharacterWeaponSettingsPrototypes')
                if isinstance(n, cfg.Struct)}
        self.assertIn('TemplateWeapon', sids)
        self.assertGreater(len(sids), 100)

    def test_each_part_reads_its_own_pak(self):
        config = Config(game=Path(GAME), repak=Path(REPAK))
        for part, (pak, _) in gametables.PARTS.items():
            with self.subTest(part):
                if not (Path(GAME) / pak).is_file():
                    self.skipTest(f'{pak} not installed')
                self.assertIsNotNone(gametables.table_text(config, part, 'ItemPrototypes'))

    @unittest.skipUnless(ZONE_KIT, 'ZONEPAK_TEST_ZONE_KIT not set')
    def test_inherited_fields_are_left_out_as_in_the_zone_kit(self):
        # 2026-11-14: TemplatePistol and the other templates with refkey=TemplateWeapon list 1 to 5 fields in the Zone
        # Kit, and 39 to 40 when the decoder writes out every inherited field.
        table = 'WeaponData/CharacterWeaponSettingsPrototypes'
        kit_file = Path(ZONE_KIT) / 'Stalker2/Content/GameLite/GameData' / f'{table}.cfg'
        kit = [n for n in cfg.parse(kit_file.read_text(encoding='utf-8-sig'), str(kit_file), strict=False)
               if isinstance(n, cfg.Struct)]
        game = {n.name: n for n in gametables.table(Config(game=Path(GAME), repak=Path(REPAK)), 'base', table)
                if isinstance(n, cfg.Struct)}
        def fields(struct):
            return [c.name if isinstance(c, cfg.Struct) else c.key for c in struct.children
                    if not isinstance(c, cfg.Unknown)]

        self.assertIn('TemplatePistol', [n.name for n in kit])
        for struct in kit:
            with self.subTest(struct.name):
                self.assertEqual(fields(game[struct.name]), fields(struct))
