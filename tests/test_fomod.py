import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from zonepak import fomod
from zonepak.project import Group, Option, Project

try:
    from lxml import etree
except ImportError:
    etree = None

SCHEMA = Path(__file__).resolve().parents[1] / 'third_party' / 'fomod-ModuleConfig.xsd'


@unittest.skipUnless(etree is not None and SCHEMA.is_file(), 'lxml is not installed')
class SchemaTest(unittest.TestCase):
    def test_module_config_matches_the_schema(self):
        root = Path(tempfile.gettempdir())
        project = Project(root, 'ZpTest', 'Zp & <Test>', '', '1.0', '1700000000', options=(
            Option(root / 'A', 'A & "B" <c>', 'A', "Tom's\nline two", root / 'fomod/a.png', True),
            Option(root / 'B', 'B', 'B'), Option(root / 'C', 'C', 'C', empty=True)))
        # libxml2 rejects the leading space in the schema's type=" xs:string" (gameDependency, line 556), which XSD's
        # whitespace collapse for QName values allows.
        schema = etree.XMLSchema(etree.fromstring(SCHEMA.read_bytes().replace(b'" xs:string"', b'"xs:string"')))
        document = etree.fromstring(fomod.module_config_xml(project))
        self.assertTrue(schema.validate(document), schema.error_log)


class GroupTest(unittest.TestCase):
    def test_groups_become_wizard_groups(self):
        root = Path(tempfile.gettempdir())
        project = Project(root, 'ZpTest', 'ZpTest', '', '1.0', '1700000000', options=(
            Option(root / 'Low', 'Low', 'Low', group='Pricing'),
            Option(root / 'Mags', 'Mags', 'Mags', default=True),
            Option(root / 'Mid', 'Mid', 'Mid', default=True, group='Pricing')),
            groups=(Group('Pricing', 'one'),))
        groups = ET.fromstring(fomod.module_config_xml(project)).findall('.//optionalFileGroups/group')
        self.assertEqual([(g.get('name'), g.get('type'), [(p.get('name'), p.find('typeDescriptor/type').get('name'))
                                                         for p in g.findall('plugins/plugin')]) for g in groups],
                         [('Pricing', 'SelectExactlyOne', [('Low', 'Optional'), ('Mid', 'Recommended')]),
                          ('Options', 'SelectAny', [('Mags', 'Recommended')])])

    def test_empty_option_has_a_flag_and_no_files(self):
        root = Path(tempfile.gettempdir())
        project = Project(root, 'ZpTest', 'ZpTest', '', '1.0', '1700000000', options=(
            Option(root / 'Std', 'Standard', 'Std', default=True, empty=True),
            Option(root / 'Low', 'Low', 'Low')))
        plugins = ET.fromstring(fomod.module_config_xml(project)).findall('.//plugin')
        self.assertEqual([[e.tag for e in p] for p in plugins],
                         [['description', 'conditionFlags', 'typeDescriptor'], ['description', 'files', 'typeDescriptor']])
        self.assertEqual(plugins[0].find('conditionFlags/flag').attrib, {'name': 'Std'})
        self.assertEqual(plugins[0].findtext('conditionFlags/flag'), 'On')


if __name__ == '__main__':
    unittest.main()
