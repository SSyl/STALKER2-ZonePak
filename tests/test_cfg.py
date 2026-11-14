import os
import unittest
from pathlib import Path

from zonepak import cfg

SAMPLE = '\ufeffTemplateMag : struct.begin\r\n' \
         '   Magazine : struct.begin\r\n' \
         '      MaxAmmo = 0 // comment\r\n' \
         '   struct.end\r\n' \
         '   Icon =\r\n' \
         'struct.end\r\n' \
         'GunA : struct.begin {refurl=../ItemPrototypes.cfg;refkey=TemplateMag;bskipref}\r\n' \
         '   [0] = First\r\n' \
         '   Old : removenode\r\n' \
         '   @Stray_Line\r\n' \
         'struct.end\r\n'


class ParseTest(unittest.TestCase):
    def test_sample(self):
        template, gun = cfg.parse(SAMPLE)
        self.assertEqual(template.find('Magazine').find('MaxAmmo').value, '0')
        self.assertEqual(gun.flags, {'refurl': '../ItemPrototypes.cfg', 'refkey': 'TemplateMag', 'bskipref': None})
        self.assertIsInstance(gun.find('Old'), cfg.Remove)
        self.assertEqual(gun.children[-1], cfg.Unknown('@Stray_Line', 10))
        self.assertEqual(cfg.canonical(cfg.parse(cfg.dumps([template, gun]))), cfg.canonical([template, gun]))
        glued = cfg.parse('A : struct.begin\nstruct.endB : struct.begin\nstruct.end\n')
        self.assertEqual([node.name for node in glued], ['A', 'B'])
        endless = cfg.parse('A : struct.begin\nstruct.endless = 1\nstruct.end\n')
        self.assertEqual(endless[0].children, [cfg.Value('struct.endless', '1', 2)])

    def test_unclosed_struct_is_an_error(self):
        with self.assertRaises(cfg.CfgError):
            cfg.parse('A : struct.begin\n  X = 1\n', 'p.cfg')
        cfg.parse('A : struct.begin\n  X = 1\n', 'p.cfg', strict=False)


@unittest.skipUnless(os.environ.get('ZONEPAK_TEST_ZONE_KIT'), 'ZONEPAK_TEST_ZONE_KIT not set')
class ZoneKitRoundTripTest(unittest.TestCase):
    def test_every_kit_cfg_round_trips(self):
        root = Path(os.environ['ZONEPAK_TEST_ZONE_KIT']) / 'Stalker2/Content/GameLite/GameData'
        files = 0
        for f in root.rglob('*.cfg'):
            text = f.read_text(encoding='utf-8-sig')
            roots = cfg.parse(text, str(f), strict=False)
            self.assertEqual(cfg.canonical(cfg.parse(cfg.dumps(roots), str(f), strict=False)), cfg.canonical(roots), str(f))
            files += 1
        self.assertGreater(files, 100000)


if __name__ == '__main__':
    unittest.main()
