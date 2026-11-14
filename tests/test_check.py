import tempfile
import unittest
from pathlib import Path

from zonepak.check import check_parts, check_project
from zonepak.tables import DLC_GAME_DATA, Tables
from zonepak.vanilla import Vanilla

ITEMS = '''TemplateMag : struct.begin
   Magazine : struct.begin
      MaxAmmo = 0
   struct.end
   Cost = 0
struct.end
GunA_Mag : struct.begin {refkey=TemplateMag}
   Magazine : struct.begin
      MaxAmmo = 15
   struct.end
struct.end
GunB_Mag : struct.begin {refkey=TemplateMag}
   Cost = 5
struct.end
'''
CORE = '''DefaultConfig : struct.begin
   Speed = 1
struct.end
'''


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.game_data = base / 'kit'
        self.game_data.mkdir()
        (self.game_data / 'ItemPrototypes.cfg').write_text(ITEMS, encoding='utf-8')
        (self.game_data / 'CoreVariables.cfg').write_text(CORE, encoding='utf-8')
        self.tables = Tables(frozenset({'ItemPrototypes'}), frozenset({'CoreVariables'}))
        self.cfg_root = base / 'cfg'

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, files: dict[str, str], dlc_tables=None):
        for rel, text in files.items():
            f = self.cfg_root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        return check_project(self.cfg_root, self.tables, Vanilla(self.game_data, self.tables), dlc_tables)

    def assertFinding(self, findings, level, text):
        self.assertTrue(any(f.level == level and text in f.message for f in findings), [str(f) for f in findings])

    def test_valid_nested_patch(self):
        findings = self.run_check({'GameData/ItemPrototypes/Mod.cfg':
                                   'GunA_Mag : struct.begin {bpatch}\n   Magazine : struct.begin {bpatch}\n'
                                   '      MaxAmmo = 12\n   struct.end\nstruct.end\n'})
        self.assertEqual(findings, [])

    def test_valid_plain_patch(self):
        findings = self.run_check({'GameData/CoreVariables.cfg_patch_Mod':
                                   'DefaultConfig : struct.begin {bpatch}\n   Speed = 2\nstruct.end\n'})
        self.assertEqual(findings, [])

    def test_missing_sid(self):
        findings = self.run_check({'GameData/ItemPrototypes/Mod.cfg': 'GunZ : struct.begin {bpatch}\nstruct.end\n'})
        self.assertFinding(findings, 'error', 'GunZ does not exist in ItemPrototypes. If it is a DLC item, put the '
                           'patch under cfg/DLCGameData/<DLC>/.')

    def test_missing_field(self):
        findings = self.run_check({'GameData/ItemPrototypes/Mod.cfg':
                                   'GunA_Mag : struct.begin {bpatch}\n   Weight = 1\nstruct.end\n'})
        self.assertFinding(findings, 'error', 'GunA_Mag.Weight does not exist in vanilla')

    def test_inherited_nested_struct(self):
        findings = self.run_check({'GameData/ItemPrototypes/Mod.cfg':
                                   'GunB_Mag : struct.begin {bpatch}\n   Magazine : struct.begin {bpatch}\n'
                                   '      MaxAmmo = 3\n   struct.end\nstruct.end\n'})
        self.assertFinding(findings, 'warning', 'GunB_Mag.Magazine is inherited through refkey')
        self.assertFalse(any(f.level == 'error' for f in findings))

    def test_unrecognized_line_in_nested_replace(self):
        findings = self.run_check({'GameData/ItemPrototypes/Mod.cfg':
                                   'GunA_Mag : struct.begin {bpatch}\n   Magazine : struct.begin\n'
                                   '      MaxAmmo = 12\n      oops\n   struct.end\nstruct.end\n'})
        self.assertEqual([str(f) for f in findings],
                         ['GameData/ItemPrototypes/Mod.cfg:4: error: unrecognized line: oops'])

    def test_refkey_to_sid_in_another_patch_file(self):
        findings = self.run_check({'GameData/ItemPrototypes/A.cfg': 'NewMag : struct.begin\n   Cost = 1\nstruct.end\n',
                                   'GameData/ItemPrototypes/B.cfg':
                                   'NewerMag : struct.begin {refkey=NewMag}\nstruct.end\n'})
        self.assertEqual(findings, [])

    def test_option_refkey_to_main_part_struct(self):
        base = Path(self.tmp.name)
        files = {'main/GameData/ItemPrototypes/Main.cfg': 'ZpMagNew : struct.begin {refkey=GunA_Mag}\nstruct.end\n'
                                                           'ZpMainNew : struct.begin {refkey=ZpOptANew}\nstruct.end\n',
                 'a/GameData/ItemPrototypes/A.cfg': 'ZpMagNew2 : struct.begin {refkey=ZpMagNew}\nstruct.end\n'
                                                    'ZpOptANew : struct.begin {refkey=GunA_Mag}\nstruct.end\n',
                 'b/GameData/ItemPrototypes/B.cfg': 'ZpOptBNew : struct.begin {refkey=ZpOptANew}\nstruct.end\n'}
        for rel, text in files.items():
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_text(text, encoding='utf-8')
        results = check_parts([base / 'main', base / 'a', base / 'b'], self.tables,
                              Vanilla(self.game_data, self.tables))
        self.assertEqual([[str(f) for f in part] for part in results], [
            ['GameData/ItemPrototypes/Main.cfg:3: error: refkey ZpOptANew does not exist in ItemPrototypes'],
            [],
            ['GameData/ItemPrototypes/B.cfg:1: error: refkey ZpOptANew does not exist in ItemPrototypes']])

    def test_option_bpatch_of_main_part_struct(self):
        base = Path(self.tmp.name)
        files = {'main/GameData/ItemPrototypes/Main.cfg': 'ZpMagNew : struct.begin {refkey=GunA_Mag}\n   Cost = 10\n'
                                                           'struct.end\n',
                 'a/GameData/ItemPrototypes/Main_A.cfg': 'ZpMagNew : struct.begin {bpatch}\n   Cost = 5\nstruct.end\n'
                                                         'ZpOptANew : struct.begin {refkey=GunA_Mag}\nstruct.end\n',
                 'b/GameData/ItemPrototypes/Main_B.cfg': 'ZpOptANew : struct.begin {bpatch}\n   Cost = 5\nstruct.end\n'}
        for rel, text in files.items():
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_text(text, encoding='utf-8')
        results = check_parts([base / 'main', base / 'a', base / 'b'], self.tables,
                              Vanilla(self.game_data, self.tables))
        self.assertEqual([[str(f) for f in part] for part in results], [
            [], [],
            ['GameData/ItemPrototypes/Main_B.cfg:1: error: ZpOptANew does not exist in ItemPrototypes. If it is a DLC '
             'item, put the patch under cfg/DLCGameData/<DLC>/.']])

    def check_main_and_option(self, main_name: str, option_name: str, option_text: str) -> list[str]:
        base = Path(self.tmp.name)
        files = {f'main/GameData/ItemPrototypes/{main_name}':
                 'GunA_Mag : struct.begin {bpatch}\n   Magazine : struct.begin {bpatch}\n      MaxAmmo = 12\n'
                 '   struct.end\nstruct.end\n',
                 f'opt/GameData/ItemPrototypes/{option_name}': option_text}
        for rel, text in files.items():
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_text(text, encoding='utf-8')
        results = check_parts([base / 'main', base / 'opt'], self.tables, Vanilla(self.game_data, self.tables))
        self.assertEqual(results[0], [])
        return [str(f) for f in results[1]]

    SAME_FIELD = ('GunA_Mag : struct.begin {bpatch}\n   Magazine : struct.begin {bpatch}\n      MaxAmmo = 30\n'
                  '   struct.end\nstruct.end\n')

    def test_option_patch_sorting_before_main_part_on_same_field(self):
        self.assertEqual(self.check_main_and_option('Mod.cfg', 'Mod-Opt.cfg', self.SAME_FIELD), [
            "GameData/ItemPrototypes/Mod-Opt.cfg:3: warning: GunA_Mag.Magazine.MaxAmmo is also set by the main "
            "part's Mod.cfg. The game uses the patch file whose name sorts last, so the main part's value wins. "
            'Give this file a name that sorts after Mod.cfg'])

    def test_option_patch_sorting_after_main_part(self):
        self.assertEqual(self.check_main_and_option('Mod.cfg', 'Mod_Opt.cfg', self.SAME_FIELD), [])

    def test_option_patch_sorting_after_only_case_sensitively(self):
        # 'b' > 'B' case-sensitively, but 'modb' < 'modc' once case is folded.
        findings = self.check_main_and_option('ModC.cfg', 'Modb.cfg', self.SAME_FIELD)
        self.assertEqual(len(findings), 1, findings)

    def test_option_patch_sorting_before_main_part_on_other_field(self):
        self.assertEqual(self.check_main_and_option('Mod.cfg', 'Mod-Opt.cfg',
                                                    'GunB_Mag : struct.begin {bpatch}\n   Cost = 9\nstruct.end\n'), [])

    def test_option_patch_with_main_part_path_is_left_to_build(self):
        self.assertEqual(self.check_main_and_option('Mod.cfg', 'mod.cfg', self.SAME_FIELD), [])

    def test_dlc_patch_is_placed_but_not_checked(self):
        dlc1 = Tables.from_pak_listing([DLC_GAME_DATA + 'DLC1/ItemPrototypes.cfg.bin',
                                        DLC_GAME_DATA + 'DLC1/NPCNames.cfg',
                                        'Stalker2/Content/GameLite/GameData/EffectPrototypes.cfg.bin'],
                                       DLC_GAME_DATA + 'DLC1/')
        findings = self.run_check({'DLCGameData/DLC1/ItemPrototypes/Mod.cfg':
                                   'DLCOnly_Mag : struct.begin {bpatch}\n   Weight = 1\nstruct.end\n',
                                   'DLCGameData/DLC1/EffectPrototypes/Mod.cfg': 'X : struct.begin\nstruct.end\n'},
                                  {'DLC1': dlc1})
        self.assertEqual([str(f) for f in findings], [
            'DLCGameData/DLC1/EffectPrototypes/Mod.cfg:0: error: EffectPrototypes is not a binarized table in the '
            'game, so this file is not loaded',
            'DLCGameData/DLC1/ItemPrototypes/Mod.cfg:1: warning: DLCOnly_Mag not checked: the Zone Kit has no DLC1 '
            'data'])

    def test_files_the_game_does_not_load_are_errors(self):
        patch = 'GunA_Mag : struct.begin {bpatch}\nstruct.end\n'
        findings = self.run_check({'GameData/Mod.cfg': patch, 'Mod.cfg': patch,
                                   'GameData/ItemPrototypes/Mod.cfg_patch_x': patch,
                                   'GameData/Missing.cfg_patch_x': patch,
                                   'GameData/ItemPrototypes/MyMod.cfg.txt': patch})
        self.assertEqual([str(f) for f in findings], [
            'GameData/ItemPrototypes/Mod.cfg_patch_x:0: error: plain-cfg patches are not read inside a binarized '
            'table folder (ItemPrototypes), so this file is not loaded',
            'GameData/ItemPrototypes/MyMod.cfg.txt:0: error: Notepad saved this file as a text file. Rename it to '
            'end in .cfg instead of .cfg.txt',
            'GameData/Missing.cfg_patch_x:0: error: Missing.cfg is not a plain table in the game, so this patch is '
            'not loaded',
            'GameData/Mod.cfg:0: error: GameData is not a binarized table in the game, so this file is not loaded',
            'Mod.cfg:0: error: outside GameData and DLCGameData/<DLC>, so the game does not load it as a patch'])

    def test_full_plain_file_replacement_is_a_warning(self):
        findings = self.run_check({'GameData/CoreVariables.cfg': 'anything at all {\n'})
        self.assertEqual([str(f) for f in findings], [
            'GameData/CoreVariables.cfg:0: warning: replaces the whole vanilla CoreVariables.cfg, so other mods cannot '
            'patch it and game updates to it are hidden. A CoreVariables.cfg_patch_<name> file changes only what it '
            'lists'])

    def test_other_files_are_warnings_and_os_files_are_ignored(self):
        findings = self.run_check({'GameData/notes.txt': 'notes', 'GameData/ItemPrototypes/desktop.ini': '',
                                   'GameData/.gitkeep': '', 'GameData/Thumbs.db': '', 'readme.md': ''})
        self.assertEqual([str(f) for f in findings], [
            f'{file}:0: warning: not a .cfg or .cfg_patch_ file, so build does not pack it'
            for file in ('GameData/notes.txt', 'readme.md')])


if __name__ == '__main__':
    unittest.main()
