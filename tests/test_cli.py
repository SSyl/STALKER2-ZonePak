import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zonepak import build, cli

GAME_DATA = 'Stalker2/Content/GameLite/GameData/'
DLC1 = 'Stalker2/Content/GameLite/DLCGameData/DLC1/'
LISTINGS = {
    'pakchunk0-Windows.pak': [GAME_DATA + 'UpgradePrototypes.cfg.bin',
                              GAME_DATA + 'AIPrototypes/ThreatPrototypes.cfg.bin', GAME_DATA + 'CoreVariables.cfg',
                              GAME_DATA + 'aiglobals.cfg', 'Stalker2/Content/Other.uasset'],
    'S2_DLC1Stalker2-Windows.pak': [DLC1 + 'ItemPrototypes.cfg.bin', DLC1 + 'NPCNames.cfg'],
}


class TablesCommandTest(unittest.TestCase):
    def run_tables(self, *args: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / 'game'
            (game / 'DLC1').mkdir(parents=True)
            (game / 'DLC1' / 'S2_DLC1Stalker2-Windows.pak').write_bytes(b'')
            (game / build.PAKCHUNK0).parent.mkdir(parents=True)
            (game / build.PAKCHUNK0).write_bytes(b'')
            config = Path(tmp) / 'config.toml'
            config.write_text('', encoding='utf-8')
            out = io.StringIO()
            with mock.patch('zonepak.tools.pak_list', lambda repak, pak: LISTINGS[pak.name]), \
                    contextlib.redirect_stdout(out):
                code = cli.main(['--config', str(config), '--game', str(game), '--repak', 'repak.exe', 'tables',
                                 *args])
            self.assertEqual(code, 0)
            return out.getvalue()

    def test_base_game(self):
        self.assertEqual(self.run_tables(), '\n'.join([
            'Binarized tables (patch with cfg/GameData/<Table>/<any name>.cfg):',
            '  AIPrototypes/ThreatPrototypes',
            '  UpgradePrototypes',
            '',
            'Plain cfg files (patch with cfg/GameData/<File>.cfg_patch_<any name>):',
            '  aiglobals.cfg',
            '  CoreVariables.cfg',
        ]) + '\n')

    def test_dlc(self):
        self.assertEqual(self.run_tables('--dlc', 'DLC1'), '\n'.join([
            'Binarized tables (patch with cfg/DLCGameData/DLC1/<Table>/<any name>.cfg):',
            '  ItemPrototypes',
            '',
            'Plain cfg files (patch with cfg/DLCGameData/DLC1/<File>.cfg_patch_<any name>):',
            '  NPCNames.cfg',
        ]) + '\n')


class TextSearchTest(unittest.TestCase):
    def test_matches_key_or_text_and_prints_text_file_lines(self):
        texts = {'sid_items_Bandage_name': 'Bandage', 'sid_a': 'Say "bandage"\nnow', 'key.with.dots': 'BANDAGE',
                 'sid_other': 'Medkit'}
        self.assertEqual(cli.search_text(texts, 'bandage'), [
            '"key.with.dots" = "BANDAGE"',
            r'sid_a = "Say \"bandage\"\nnow"',
            'sid_items_Bandage_name = "Bandage"',
        ])


if __name__ == '__main__':
    unittest.main()
