import tempfile
import unittest
from pathlib import Path

from zonepak.project import Config, ProjectError, load_config, load_project, new_project


class ByteOrderMarkTest(unittest.TestCase):
    def test_config_and_project_files_accept_a_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'config.toml'
            config.write_text("game = 'C:\\Game'\n", encoding='utf-8-sig')
            self.assertEqual(load_config(config).game, Path('C:\\Game'))
            root = new_project(Path(tmp), 'ZpTest', now=lambda: 1700000000)
            project_file = root / 'zonepak.toml'
            project_file.write_text(project_file.read_text(encoding='utf-8'), encoding='utf-8-sig')
            self.assertEqual(load_project(root).name, 'ZpTest')


class HintTest(unittest.TestCase):
    def test_missing_project_hint_names_project_option(self):
        with tempfile.TemporaryDirectory() as tmp,                 self.assertRaisesRegex(ProjectError, r'Run `python -m zonepak --project <parent folder> new <Name>`'):
            load_project(Path(tmp))

    def test_missing_config_file_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            with self.assertRaisesRegex(ProjectError, r'zone_kit is not set, and the config file .* does not exist yet'):
                Config(source=path).require('zone_kit')
            path.write_text("game = 'C:/Game'\n", encoding='utf-8')
            with self.assertRaisesRegex(ProjectError, r'zone_kit is not set\. Add it to'):
                load_config(path).require('zone_kit')

    def test_flags_are_suggested_only_on_the_command_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            path.write_text("game = 'C:/Game'\n", encoding='utf-8')
            with self.assertRaises(ProjectError) as library:
                load_config(path).require('zone_kit')
            self.assertNotIn('--zone-kit', str(library.exception))
            with self.assertRaisesRegex(ProjectError, r'or pass --zone-kit\.'):
                Config(source=path, cli=True).require('zone_kit')


class ConfigFileTest(unittest.TestCase):
    def test_named_config_file_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ProjectError, r'config\.toml not found$'):
            load_config(Path(tmp) / 'config.toml')

    def test_values_must_be_path_strings(self):
        for line in ('game = 3', "game = ''"):
            with tempfile.TemporaryDirectory() as tmp, self.subTest(line):
                path = Path(tmp) / 'config.toml'
                path.write_text(line + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ProjectError, r'config\.toml: game must be a path string$'):
                    load_config(path)


class ManifestFieldTest(unittest.TestCase):
    def load_with(self, line):
        with tempfile.TemporaryDirectory() as tmp:
            root = new_project(Path(tmp), 'ZpTest', now=lambda: 1700000000)
            path = root / 'zonepak.toml'
            text = path.read_text(encoding='utf-8')
            key = line.split(' =')[0]
            kept = [old for old in text.splitlines() if not old.startswith(f'{key} =')]
            path.write_text('\n'.join(kept + [line]) + '\n', encoding='utf-8')
            return load_project(root)

    def test_version_rule(self):
        for version in ('1', '1.0', '0.1', '1.2.3', '10.20.30'):
            self.assertEqual(self.load_with(f'version = "{version}"').version, version)
        for line in ('version = "v1.0"', 'version = "1.0-beta"', 'version = "1.2.3.4"', 'version = "1..2"',
                     'version = ""', 'version = 1.10', 'version = "１.０"'):
            with self.subTest(line), self.assertRaisesRegex(
                    ProjectError, r'zonepak\.toml: version must be one to three numbers separated by dots'):
                self.load_with(line)

    def test_blank_author_and_website_count_as_unset(self):
        self.assertEqual(self.load_with('author = "  "').author, '')
        self.assertEqual(self.load_with('website = " https://example.com "').website, 'https://example.com')

    def test_text_for_the_fomod_rejects_control_characters(self):
        with self.assertRaisesRegex(ProjectError, r'zonepak\.toml: description contains a control character '
                                                  r'\(U\+000C\) that the FOMOD files cannot hold\. In double quotes, '
                                                  r'a backslash starts an escape such as \\f'):
            self.load_with(r'description = "see ~mods\folder"')

    def test_nexus_id_must_be_a_whole_number(self):
        self.assertEqual(self.load_with('nexus_id = 164').nexus_id, 164)
        for line in ('nexus_id = "164"', 'nexus_id = 1.5', 'nexus_id = true', 'nexus_id = 0'):
            with self.subTest(line), self.assertRaisesRegex(ProjectError,
                                                            r'zonepak\.toml: nexus_id must be a whole number'):
                self.load_with(line)

    def test_database_id_is_ten_digits(self):
        self.assertEqual(self.load_with('database_id = "0123456789"').database_id, '0123456789')
        for line in ('database_id = "170000000"', 'database_id = "17000000000"', 'database_id = "170000000x"'):
            with self.subTest(line), self.assertRaisesRegex(ProjectError,
                                                            r'zonepak\.toml: database_id must be 10 digits'):
                self.load_with(line)

    def test_name_rule(self):
        for line, message in (('name = "Zp-Test"', r"mod name 'Zp-Test' must use only letters, digits and underscores"),
                              ('name = "Stage"', r"mod name 'Stage' is reserved, because ZonePak uses build/stage/")):
            with self.subTest(line), self.assertRaisesRegex(ProjectError, message):
                self.load_with(line)

    def test_unknown_key(self):
        with self.assertRaisesRegex(ProjectError, r'zonepak\.toml: unknown keys fill_game_txt$'):
            self.load_with('fill_game_txt = true')

    def test_text_settings(self):
        project = self.load_with('fill_game_text = true')
        self.assertTrue(project.fill_game_text)
        self.assertEqual(self.load_with('copy_new_text = "de"').copy_new_text, 'de')
        for line, message in (('fill_game_text = "true"', 'fill_game_text must be true or false, without quotes'),
                              ('copy_new_text = "german"', 'copy_new_text must be a culture in quotes, one of ar, ')):
            with self.subTest(line), self.assertRaisesRegex(ProjectError, r'zonepak\.toml: ' + message):
                self.load_with(line)


class OptionFieldTest(unittest.TestCase):
    def load_with(self, options, files=()):
        with tempfile.TemporaryDirectory() as tmp:
            root = new_project(Path(tmp), 'ZpTest', now=lambda: 1700000000)
            for rel in files:
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_bytes(b'')
            with open(root / 'zonepak.toml', 'a', encoding='utf-8') as f:
                f.write(options)
            return load_project(root)

    def test_valid_options(self):
        project = self.load_with('[[option]]\nname = " A & B "\nfolder = "Opt_1"\nimage = "fomod/a.png"\n'
                                 'default = true\n\n[[option]]\nname = "C"\nfolder = "Opt2"\ndescription = "D"\n',
                                 ['fomod/a.png'])
        self.assertEqual([(o.name, o.folder, o.description, o.image.name if o.image else None, o.default)
                          for o in project.options],
                         [('A & B', 'Opt_1', '', 'a.png', True), ('C', 'Opt2', 'D', None, False)])
        self.assertEqual(project.options[0].cfg_dir, project.root / 'Opt_1' / 'cfg')
        self.assertEqual([o.empty for o in project.options], [False, False])

    def test_options_folder(self):
        project = self.load_with('options_folder = "options"\n\n[[option]]\nname = "A"\nfolder = "Opt"\n')
        self.assertEqual(project.options[0].folder, 'Opt')
        self.assertEqual(project.options[0].cfg_dir, project.root / 'options' / 'Opt' / 'cfg')

    def test_bad_options_folder(self):
        for value in ('"cfg"', '"a/b"', '3'):
            with self.subTest(value=value), \
                    self.assertRaisesRegex(ProjectError, 'options_folder must be a folder name'):
                self.load_with(f'options_folder = {value}\n')

    def test_empty_option(self):
        project = self.load_with('[[option]]\nname = "A"\nfolder = "Opt"\nempty = true\n', [])
        self.assertTrue(project.options[0].empty)

    def test_bad_options(self):
        one = '[[option]]\nname = "A"\nfolder = "Opt"\n'
        cases = [
            ('[option]\nname = "A"\nfolder = "Opt"\n', [],
             r'write each option as a table that starts with \[\[option\]\]'),
            (one + 'colour = "red"\n', [], r'option 1: unknown keys colour'),
            ('[[option]]\nfolder = "Opt"\n', [], r'option 1: name is required, as text in quotes'),
            ('[[option]]\nname = "A"\nfolder = "My Opt"\n', [], r'option 1: folder is required and must use only'),
            ('[[option]]\nname = "A"\nfolder = "MAIN"\n', [], r"option 1: folder 'MAIN' is reserved"),
            (one + one.replace('"Opt"', '"opt"'), [], r"option 2: folder 'opt' is already used by option 1"),
            (one + 'description = 5\n', [], r'option 1: description must be text in quotes'),
            (one + 'default = "yes"\n', [], r'option 1: default must be true or false, without quotes'),
            (one + 'empty = 1\n', [], r'option 1: empty must be true or false, without quotes'),
            (one + r'description = "C:\folder"' + '\n', [],
             r'option 1: description contains a control character \(U\+000C\) that the FOMOD files'),
            (one + 'image = "a.gif"\n', ['a.gif'], r'option 1: image must be the path of a \.png or \.jpg file'),
            (one + 'image = "../a.png"\n', [], r'option 1: image must be a path inside the project folder'),
            (one + 'image = "a.png"\n', [], r'option 1: image .*a\.png not found'),
            (one + 'image = "x/a.png"\n' + one.replace('"Opt"', '"Opt2"') + 'image = "y/A.png"\n',
             ['x/a.png', 'y/A.png'], r'option 2: image file name A\.png is already used by the image of option 1'),
            (one, ['Opt/text/en.toml'], r'option 1: options are cfg-only, so Opt/text/ is not allowed'),
        ]
        for options, files, message in cases:
            with self.subTest(message), self.assertRaisesRegex(ProjectError, r'zonepak\.toml: ' + message):
                self.load_with(options, files)

    def test_absolute_image_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'a.png'
            image.write_bytes(b'')
            with self.assertRaisesRegex(ProjectError, r'option 1: image must be a path inside the project folder'):
                self.load_with(f"[[option]]\nname = \"A\"\nfolder = \"Opt\"\nimage = '{image.as_posix()}'\n")

    def test_valid_groups(self):
        project = self.load_with('[[group]]\nname = "Pricing"\nselect = "one"\n\n'
                                 '[[option]]\nname = "Low"\nfolder = "Low"\ngroup = "pricing"\n\n'
                                 '[[option]]\nname = "Mags"\nfolder = "Mags"\ndefault = true\n\n'
                                 '[[option]]\nname = "Mid"\nfolder = "Mid"\ngroup = "Pricing"\ndefault = true\n')
        self.assertEqual([(g.name, g.select) for g in project.groups], [('Pricing', 'one')])
        self.assertEqual([(group.name, [o.folder for o in options]) for group, options in project.option_groups()],
                         [('Pricing', ['Low', 'Mid']), ('Options', ['Mags'])])

    def test_bad_groups(self):
        group = '[[group]]\nname = "Pricing"\nselect = "one"\n'
        low = '[[option]]\nname = "Low"\nfolder = "Low"\ngroup = "Pricing"\n'
        mid = low.replace('Low', 'Mid')
        cases = [
            ('[group]\nname = "Pricing"\n', r'write each group as a table that starts with \[\[group\]\]'),
            (group + 'kind = "x"\n' + low + 'default = true\n', r'group 1: unknown keys kind'),
            ('[[group]]\nselect = "one"\n', r'group 1: name is required, as text in quotes'),
            ('[[group]]\nname = "options"\n', r"group 1: name 'options' is reserved for options without a group"),
            (group + group.replace('Pricing', 'PRICING'), r"group 2: name 'PRICING' is already used by group 1"),
            (group.replace('"one"', '"all"'), r'group 1: select must be "any" or "one"'),
            (low.replace('Pricing', 'Prices'), r'option 1: group must be the name of a \[\[group\]\] table'),
            (group, r"group 'Pricing' has no options"),
            (group + low + mid, r'group \'Pricing\' has select = "one", so exactly one of its options needs default'),
            (group + low + 'default = true\n' + mid + 'default = true\n',
             r'group \'Pricing\' has select = "one", so exactly one of its options needs default'),
        ]
        for text, message in cases:
            with self.subTest(message), self.assertRaisesRegex(ProjectError, r'zonepak\.toml: ' + message):
                self.load_with(text)


if __name__ == '__main__':
    unittest.main()
