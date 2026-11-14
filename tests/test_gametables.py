import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zonepak import build, cfg, gametables
from zonepak.project import Config

REPAK = os.environ.get('ZONEPAK_TEST_REPAK')
GAME = os.environ.get('ZONEPAK_TEST_GAME')


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
