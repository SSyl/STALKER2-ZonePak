import os
import unittest
from pathlib import Path

from zonepak import locdb
from zonepak.locres import GameText

REPAK = os.environ.get('ZONEPAK_TEST_REPAK')
GAME = os.environ.get('ZONEPAK_TEST_GAME')
# Has en text in the game but no de entry.
UNTRANSLATED = 'sid_AContent_dlcProfile_dlc01_TTL'


@unittest.skipUnless(REPAK and GAME, 'ZONEPAK_TEST_REPAK and ZONEPAK_TEST_GAME not set')
class GameTextTest(unittest.TestCase):
    def test_fill_cultures(self):
        game = GameText(Path(REPAK), Path(GAME))
        self.assertEqual(game.culture('en')['sid_items_Bandage_name'], 'Bandage')
        self.assertNotIn(UNTRANSLATED, game.culture('de'))
        entries = {'sid_items_Bandage_name': {'en': 'Bandage [Zp]'}, UNTRANSLATED: {'ru': 'Ru [Zp]'},
                   'zp_new_key': {'de': 'Neu', 'fr': 'Nouveau'}}

        filled, from_game, copied = locdb.fill_cultures(entries, game.culture, True, '')
        self.assertEqual(set(filled['sid_items_Bandage_name']), set(locdb.CULTURES))
        self.assertEqual(filled['sid_items_Bandage_name']['en'], 'Bandage [Zp]')
        self.assertEqual(filled['sid_items_Bandage_name']['de'], 'Verband')
        self.assertEqual(filled['sid_items_Bandage_name']['uk'], game.culture('uk')['sid_items_Bandage_name'])
        self.assertEqual(filled[UNTRANSLATED]['de'], game.culture('en')[UNTRANSLATED])
        self.assertEqual(filled['zp_new_key'], entries['zp_new_key'])
        self.assertEqual((from_game, copied), (34, 0))

        filled, from_game, copied = locdb.fill_cultures(entries, game.culture, False, 'fr')
        self.assertEqual(filled['sid_items_Bandage_name'], entries['sid_items_Bandage_name'])
        self.assertEqual((filled['zp_new_key']['de'], filled['zp_new_key']['en']), ('Neu', 'Nouveau'))
        self.assertEqual((from_game, copied), (0, 16))


if __name__ == '__main__':
    unittest.main()
