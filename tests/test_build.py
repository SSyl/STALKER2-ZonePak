import json
import os
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest import mock

from zonepak import build, tools
from zonepak.project import Config, ProjectError, load_project, new_project

REPAK = os.environ.get('ZONEPAK_TEST_REPAK')
RETOC = os.environ.get('ZONEPAK_TEST_RETOC')
GAME = os.environ.get('ZONEPAK_TEST_GAME')
PATCH_A = 'GunUDP_MagDefault : struct.begin {bpatch}\r\n   Magazine : struct.begin {bpatch}\r\n      MaxAmmo = 12\r\n   struct.end\r\nstruct.end\r\n'
PATCH_B = 'GunUDP_Upgrade_Barrel_1 : struct.begin {bpatch}\r\nstruct.end\r\n'


class BuildTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = new_project(Path(self.tmp.name), 'ZpTest', now=lambda: 1700000000)
        fake_pak = Path(self.tmp.name) / 'game' / build.PAKCHUNK0
        fake_pak.parent.mkdir(parents=True)
        fake_pak.write_bytes(b'')
        self.config = Config(repak=Path(REPAK) if REPAK else None, retoc=Path(RETOC) if RETOC else None,
                             game=Path(GAME) if GAME else None)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(text.encode('utf-8'))


class RunCheckTest(BuildTestBase):
    def test_wrong_zone_kit_path(self):
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        with self.assertRaisesRegex(ProjectError, 'Is zone_kit set to the Zone Kit install folder'):
            build.run_check(load_project(self.root), Config(zone_kit=Path(self.tmp.name) / 'NotTheKit'))

    def test_wrong_game_path_names_the_setting(self):
        self.write('text/en.toml', 'sid_items_Bandage_name = "Bandage [Zp]"\n')
        config = Config(game=Path(self.tmp.name) / 'NotTheGame', repak=Path('repak.exe'))
        with mock.patch('zonepak.tools.pak_get', side_effect=AssertionError('repak ran')), \
                self.assertRaisesRegex(ProjectError, r'pakchunk0-Windows\.pak not found\. Is game set to'):
            build.run_check(load_project(self.root), config)

    def test_text_only_mod_needs_no_zone_kit_or_game_tables(self):
        self.write('text/en.toml', 'sid_items_Bandage_name = "Bandage [Zp]"\n')
        game = mock.Mock()
        game.culture.return_value = {'sid_items_Bandage_name': 'Bandage'}
        with mock.patch('zonepak.build.game_tables', side_effect=AssertionError('game tables listed')), \
                mock.patch('zonepak.build.game_text', lambda config: game):
            findings = build.run_check(load_project(self.root), Config(game=Path(self.tmp.name) / 'game'))
        self.assertEqual(findings, [])

    def test_os_files_in_cfg_do_not_make_it_a_cfg_mod(self):
        self.write('text/en.toml', 'sid_items_Bandage_name = "Bandage [Zp]"\n')
        self.write('cfg/Thumbs.db', 'explorer')
        self.write('cfg/GameData/.gitkeep', '')
        game = mock.Mock()
        game.culture.return_value = {'sid_items_Bandage_name': 'Bandage'}
        with mock.patch('zonepak.build.game_tables', side_effect=AssertionError('game tables listed')), \
                mock.patch('zonepak.build.game_text', lambda config: game):
            findings = build.run_check(load_project(self.root), Config(game=Path(self.tmp.name) / 'game'))
        self.assertEqual(findings, [])

    def test_stray_file_in_cfg_still_needs_zone_kit(self):
        self.write('cfg/notes.txt', 'not a patch')
        with self.assertRaisesRegex(ProjectError, r'zone_kit is not set'):
            build.run_check(load_project(self.root), Config())

    def test_broken_text_file_is_an_error(self):
        kit = Path(self.tmp.name) / 'kit'
        (kit / build.KIT_GAME_DATA).mkdir(parents=True)
        config = Config(zone_kit=kit, game=Path(self.tmp.name) / 'game', repak=Path('repak.exe'))
        self.write('text/en.toml', 'sid_items_Bandage_name = "no closing quote\n')
        with mock.patch('zonepak.tools.pak_list', lambda repak, pak: []):
            findings = build.run_check(load_project(self.root), config)
            self.assertEqual([(f.level, f.file, f.line) for f in findings], [('error', 'text/en.toml', 0)])
            self.assertIn('(at line 1, column', findings[0].message)
            with self.assertRaisesRegex(build.BuildError, r'1 error\(s\) in patch or text files'):
                build.build(load_project(self.root), config)

    def test_text_left_without_cultures_is_a_warning(self):
        kit = Path(self.tmp.name) / 'kit'
        (kit / build.KIT_GAME_DATA).mkdir(parents=True)
        config = Config(zone_kit=kit, game=Path(self.tmp.name) / 'game', repak=Path('repak.exe'))
        self.write('text/en.toml', 'sid_items_Bandage_name = "Bandage [Zp]"\nsid_items_Bandaeg_name = "Typo"\n')
        self.write('text/de.toml', 'zp_new_key = "Neu"\n')
        game = mock.Mock()
        game.culture.return_value = {'sid_items_Bandage_name': 'Bandage'}

        def check():
            with mock.patch('zonepak.tools.pak_list', lambda repak, pak: []), \
                    mock.patch('zonepak.build.game_text', lambda config: game):
                findings = build.run_check(load_project(self.root), config)
            return [(f.file, f.message.split(' ', 1)[0]) for f in findings], findings

        self.assertFalse(load_project(self.root).fill_game_text)
        found, findings = check()
        self.assertEqual(found, [('text/en.toml', 'sid_items_Bandaeg_name'), ('text/de.toml', 'zp_new_key')])
        self.assertIn('is not one of the game', findings[0].message)
        self.assertIn('set copy_new_text = "de"', findings[1].message)

        self.write('zonepak.toml', (self.root / 'zonepak.toml').read_text(encoding='utf-8') + 'copy_new_text = "de"\n')
        found, findings = check()
        self.assertEqual(found, [('text/en.toml', 'sid_items_Bandaeg_name')])

    def test_option_findings_name_the_option_folder(self):
        kit = Path(self.tmp.name) / 'kit'
        (kit / build.KIT_GAME_DATA).mkdir(parents=True)
        config = Config(zone_kit=kit, game=Path(self.tmp.name) / 'game', repak=Path('repak.exe'))
        self.write('zonepak.toml', (self.root / 'zonepak.toml').read_text(encoding='utf-8')
                   + '[[option]]\nname = "A"\nfolder = "Opt"\n\n[[option]]\nname = "B"\nfolder = "Empty"\n')
        self.write('Opt/cfg/GameData/Mod.cfg', PATCH_B)
        with mock.patch('zonepak.tools.pak_list', lambda repak, pak: []):
            findings = build.run_check(load_project(self.root), config)
        self.assertEqual([str(f) for f in findings], [
            'Opt/cfg/GameData/Mod.cfg:0: error: GameData is not a binarized table in the game, so this file is not '
            'loaded',
            'Empty/cfg:0: error: no patch files under Empty/cfg/GameData/ or Empty/cfg/DLCGameData/<DLC>/, so the '
            'option installs nothing. Add empty = true if that is intended'])

    def test_empty_option(self):
        kit = Path(self.tmp.name) / 'kit'
        (kit / build.KIT_GAME_DATA).mkdir(parents=True)
        config = Config(zone_kit=kit, game=Path(self.tmp.name) / 'game', repak=Path('repak.exe'))
        self.write('zonepak.toml', (self.root / 'zonepak.toml').read_text(encoding='utf-8')
                   + '[[option]]\nname = "A"\nfolder = "Std"\nempty = true\n\n'
                     '[[option]]\nname = "B"\nfolder = "Full"\nempty = true\n')
        self.write('Full/cfg/GameData/ItemPrototypes/Mod_Full.cfg', PATCH_B)
        with mock.patch('zonepak.tools.pak_list', lambda repak, pak: []):
            findings = build.run_check(load_project(self.root), config)
        self.assertEqual([str(f) for f in findings if f.file in ('Std/cfg', 'Full/cfg')], [
            'Full/cfg:0: error: the option has empty = true, so build leaves out its patch files. Remove '
            'empty = true, or the files'])

    def test_same_game_path_in_two_parts_is_a_warning(self):
        kit = Path(self.tmp.name) / 'kit'
        (kit / build.KIT_GAME_DATA).mkdir(parents=True)
        config = Config(zone_kit=kit, game=Path(self.tmp.name) / 'game', repak=Path('repak.exe'))
        self.write('zonepak.toml', (self.root / 'zonepak.toml').read_text(encoding='utf-8')
                   + '[[option]]\nname = "A"\nfolder = "Opt"\n')
        self.write('cfg/GameData/ItemPrototypes/Options.cfg', PATCH_B)
        self.write('Opt/cfg/GameData/ItemPrototypes/options.cfg', PATCH_B)
        with mock.patch('zonepak.tools.pak_list', lambda repak, pak: []):
            findings = build.run_check(load_project(self.root), config)
        self.assertEqual([str(f) for f in findings if f.level == 'warning'], [
            'Opt/cfg/GameData/ItemPrototypes/options.cfg:0: warning: has the same game path as '
            'GameData/ItemPrototypes/Options.cfg, so the game loads only one of them'])


class FailedBuildTest(BuildTestBase):
    def test_failed_build_keeps_the_previous_build(self):
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        self.write('build/ZpTest/ZpTestStalker2-Windows-OverrideContent.pak', 'previous build')
        config = Config(repak=Path(self.tmp.name) / 'missing' / 'repak.exe')
        with self.assertRaisesRegex(tools.ToolError, 'cannot run'):
            build.build(load_project(self.root), config, findings=[])
        self.assertEqual((self.root / 'build/ZpTest/ZpTestStalker2-Windows-OverrideContent.pak').read_text(),
                         'previous build')
        self.assertEqual(sorted(p.name for p in self.root.iterdir() if p.name.startswith('build')), ['build'])


@unittest.skipUnless(REPAK, 'ZONEPAK_TEST_REPAK not set')
class CfgOnlyBuildTest(BuildTestBase):
    def test_single_table(self):
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        flat = build.build(load_project(self.root), self.config, findings=[])
        pak = flat / 'ZpTestStalker2-Windows-OverrideContent.pak'
        self.assertEqual(sorted(p.name for p in flat.iterdir()), [pak.name])
        self.assertEqual(tools.pak_mount_point(self.config.repak, pak),
                         '../../../Stalker2/Content/GameLite/GameData/ItemPrototypes/')

    def test_two_tables_one_pak_and_outputs(self):
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        self.write('cfg/GameData/UpgradePrototypes/ZpTest.cfg', PATCH_B)
        toml = (self.root / 'zonepak.toml').read_text(encoding='utf-8').replace('author = ""', 'author = "Zp Author"')
        self.write('zonepak.toml', toml + 'nexus_id = 164\n')
        flat = build.build(load_project(self.root), self.config, findings=[])
        pak = flat / 'ZpTestStalker2-Windows-OverrideContent.pak'
        self.assertEqual(tools.pak_mount_point(self.config.repak, pak), '../../../Stalker2/Content/GameLite/GameData/')
        out = Path(self.tmp.name) / 'unpacked'
        tools.pak_unpack(self.config.repak, pak, out)
        unpacked = out / 'Stalker2/Content/GameLite/GameData'
        self.assertEqual((unpacked / 'ItemPrototypes/ZpTest.cfg').read_bytes(), PATCH_A.encode())
        self.assertEqual((unpacked / 'UpgradePrototypes/ZpTest.cfg').read_bytes(), PATCH_B.encode())

        self.assertEqual(sorted(p.name for p in (self.root / 'build').iterdir()),
                         ['ZpTest', 'ZpTest-1.0.zip', 'build.json'])
        with zipfile.ZipFile(self.root / 'build/ZpTest-1.0.zip') as z:
            self.assertEqual(z.namelist(), ['ZpTest/ZpTestStalker2-Windows-OverrideContent.pak'])
        info = json.loads((self.root / 'build/build.json').read_text(encoding='utf-8'))
        self.assertEqual((info['version'], info['author'], info['nexus_id']), ('1.0', 'Zp Author', 164))
        self.assertNotIn('website', info)
        self.assertFalse((self.root / 'build/stage').exists())

    def test_base_and_dlc_in_one_pak(self):
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        self.write('cfg/DLCGameData/DLC1/ItemPrototypes/ZpTest.cfg', PATCH_B)
        self.write('cfg/DLCGameData/stray.cfg', PATCH_B)
        flat = build.build(load_project(self.root), self.config, findings=[])
        pak = flat / 'ZpTestStalker2-Windows-OverrideContent.pak'
        self.assertEqual(tools.pak_mount_point(self.config.repak, pak), '../../../Stalker2/Content/GameLite/')
        out = Path(self.tmp.name) / 'unpacked'
        tools.pak_unpack(self.config.repak, pak, out)
        packed = sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
        self.assertEqual(packed, ['Stalker2/Content/GameLite/DLCGameData/DLC1/ItemPrototypes/ZpTest.cfg',
                                  'Stalker2/Content/GameLite/GameData/ItemPrototypes/ZpTest.cfg'])

    def test_options_build_a_fomod(self):
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        self.write('Barrel/cfg/GameData/UpgradePrototypes/ZpTest_Barrel.cfg', PATCH_B)
        self.write('Late_Mag/cfg/DLCGameData/DLC1/ItemPrototypes/ZpTest_Late.cfg', PATCH_A)
        self.write('fomod/barrel.png', 'png')
        toml = (self.root / 'zonepak.toml').read_text(encoding='utf-8').replace('author = ""', 'author = "Zp & Co"')
        self.write('zonepak.toml', toml + 'nexus_id = 164\n\n'
                   '[[option]]\nname = "Barrel <&> \\"quoted\\""\nfolder = "Barrel"\ndescription = "Tom\'s & <b>"\n'
                   'image = "fomod/barrel.png"\ndefault = true\n\n[[option]]\nname = "Late"\nfolder = "Late_Mag"\n'
                   '\n[[option]]\nname = "Plain"\nfolder = "Plain"\nempty = true\ndefault = true\n')
        flat = build.build(load_project(self.root), self.config, findings=[])
        main_pak, barrel_pak, late_pak = ('ZpTestStalker2-Windows-OverrideContent.pak',
                                          'ZpTest_BarrelStalker2-Windows-OverrideContent.pak',
                                          'ZpTest_Late_MagStalker2-Windows-OverrideContent.pak')
        self.assertEqual(sorted(p.name for p in flat.iterdir()), [main_pak, barrel_pak])
        info = json.loads((self.root / 'build/build.json').read_text(encoding='utf-8'))
        self.assertEqual(sorted(info['files']), [main_pak, barrel_pak])
        self.assertEqual(tools.pak_mount_point(self.config.repak, flat / barrel_pak),
                         '../../../Stalker2/Content/GameLite/GameData/UpgradePrototypes/')

        with zipfile.ZipFile(self.root / 'build/ZpTest-1.0.zip') as z:
            self.assertEqual(z.namelist(), ['fomod/info.xml', 'fomod/ModuleConfig.xml', 'fomod/images/barrel.png',
                                            f'Main/{main_pak}', f'Barrel/{barrel_pak}', f'Late_Mag/{late_pak}'])
            self.assertEqual(z.read(f'Barrel/{barrel_pak}'), (flat / barrel_pak).read_bytes())
            late = Path(self.tmp.name) / late_pak
            late.write_bytes(z.read(f'Late_Mag/{late_pak}'))
            config_xml = z.read('fomod/ModuleConfig.xml')
            info_xml = ET.fromstring(z.read('fomod/info.xml'))
        self.assertEqual(tools.pak_mount_point(self.config.repak, late),
                         '../../../Stalker2/Content/GameLite/DLCGameData/DLC1/ItemPrototypes/')
        self.assertEqual([(e.tag, e.text) for e in info_xml],
                         [('Name', 'ZpTest'), ('Author', 'Zp & Co'), ('Version', '1.0'), ('Id', '164')])

        self.assertTrue(config_xml.startswith(b'<?xml version="1.0" encoding="utf-8"?>'))
        config = ET.fromstring(config_xml)
        self.assertEqual(config.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation'),
                         'http://qconsulting.ca/fo3/ModConfig5.0.xsd')
        self.assertEqual([e.tag for e in config], ['moduleName', 'requiredInstallFiles', 'installSteps'])
        self.assertEqual([config.find(path).get('order') for path in (
            'installSteps', 'installSteps/installStep/optionalFileGroups',
            'installSteps/installStep/optionalFileGroups/group/plugins')], ['Explicit'] * 3)
        self.assertEqual(config.findtext('moduleName'), 'ZpTest')
        self.assertEqual([e.attrib for e in config.find('requiredInstallFiles')],
                         [{'source': 'Main', 'destination': ''}])
        group = config.find('installSteps/installStep/optionalFileGroups/group')
        self.assertEqual(group.get('type'), 'SelectAny')
        plugins = group.findall('plugins/plugin')
        self.assertEqual([[e.tag for e in p] for p in plugins],
                         [['description', 'image', 'files', 'typeDescriptor'],
                          ['description', 'files', 'typeDescriptor'],
                          ['description', 'conditionFlags', 'typeDescriptor']])
        self.assertEqual([(p.get('name'), p.findtext('description'), p.find('files/folder').attrib,
                           p.find('typeDescriptor/type').get('name')) for p in plugins[:2]], [
            ('Barrel <&> "quoted"', "Tom's & <b>", {'source': 'Barrel', 'destination': '', 'priority': '0'},
             'Recommended'),
            ('Late', '', {'source': 'Late_Mag', 'destination': '', 'priority': '0'}, 'Optional')])
        self.assertEqual(plugins[0].find('image').get('path'), 'fomod/images/barrel.png')


@unittest.skipUnless(REPAK and RETOC and GAME, 'ZONEPAK_TEST_REPAK, ZONEPAK_TEST_RETOC and ZONEPAK_TEST_GAME not set')
class TextBuildTest(BuildTestBase):
    def test_text_and_cfg_in_one_container(self):
        self.write('text/en.toml', 'sid_items_Bandage_name = "Bandage [ZpTest]"\n')
        self.write('cfg/GameData/ItemPrototypes/ZpTest.cfg', PATCH_A)
        flat = build.build(load_project(self.root), self.config, findings=[])
        base = 'ZpTestStalker2-Windows-OverrideContent'
        self.assertEqual(sorted(p.name for p in flat.iterdir()), [f'{base}.pak', f'{base}.ucas', f'{base}.utoc'])
        chunks = tools.retoc_list(self.config.retoc, flat / f'{base}.utoc')
        self.assertEqual(sum('ExportBundleData' in c for c in chunks), 1)
        self.assertEqual(sum('ContainerHeader' in c for c in chunks), 1)
        self.assertIn(b'/Game/Autogenerated_1700000000_LocalizationDatabase', (flat / f'{base}.ucas').read_bytes())
        self.assertEqual(tools.pak_mount_point(self.config.repak, flat / f'{base}.pak'),
                         '../../../Stalker2/Content/GameLite/')


if __name__ == '__main__':
    unittest.main()
