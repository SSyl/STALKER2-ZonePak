"""fomod/info.xml and fomod/ModuleConfig.xml for a mod with options."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from .project import GROUP_SELECT, Project

# Vortex picks the schema version from this exact URL and validates against its own copy of that schema.
SCHEMA_LOCATION = 'http://qconsulting.ca/fo3/ModConfig5.0.xsd'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
MAIN_FOLDER = 'Main'
IMAGES = 'fomod/images'


def _to_bytes(root: ET.Element) -> bytes:
    ET.indent(root, space='    ')
    # Vortex strips only a double-quoted encoding declaration before parsing, and ElementTree writes a single-quoted
    # one, which Vortex then fails on.
    return ('<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n').encode('utf-8')


def info_xml(project: Project) -> bytes:
    root = ET.Element('fomod')
    for tag, value in (('Name', project.friendly_name), ('Author', project.author), ('Version', project.version),
                       ('Id', str(project.nexus_id or '')), ('Website', project.website),
                       ('Description', project.description)):
        if value.strip():
            ET.SubElement(root, tag).text = value.strip()
    return _to_bytes(root)


def module_config_xml(project: Project) -> bytes:
    """Elements follow the schema's sequence order, which Vortex enforces."""
    root = ET.Element('config', {'xmlns:xsi': XSI, 'xsi:noNamespaceSchemaLocation': SCHEMA_LOCATION})
    ET.SubElement(root, 'moduleName').text = project.friendly_name.strip() or project.name
    required = ET.SubElement(root, 'requiredInstallFiles')
    ET.SubElement(required, 'folder', source=MAIN_FOLDER, destination='')
    steps = ET.SubElement(root, 'installSteps', order='Explicit')
    step = ET.SubElement(steps, 'installStep', name='Options')
    groups = ET.SubElement(step, 'optionalFileGroups', order='Explicit')
    for group, options in project.option_groups():
        element = ET.SubElement(groups, 'group', name=group.name, type=GROUP_SELECT[group.select])
        # Without order="Explicit" the managers sort the options by name.
        plugins = ET.SubElement(element, 'plugins', order='Explicit')
        for option in options:
            plugin = ET.SubElement(plugins, 'plugin', name=option.name)
            ET.SubElement(plugin, 'description').text = option.description
            if option.image:
                ET.SubElement(plugin, 'image', path=f'{IMAGES}/{option.image.name}')
            if option.empty:
                # The schema requires files or conditionFlags on every plugin.
                flags = ET.SubElement(plugin, 'conditionFlags')
                ET.SubElement(flags, 'flag', name=option.folder).text = 'On'
            else:
                files = ET.SubElement(plugin, 'files')
                # A Stalker2\... destination makes the STALKER 2 Vortex extension deploy the files to the wrong
                # folder.
                ET.SubElement(files, 'folder', source=option.folder, destination='', priority='0')
            descriptor = ET.SubElement(plugin, 'typeDescriptor')
            ET.SubElement(descriptor, 'type', name='Recommended' if option.default else 'Optional')
    return _to_bytes(root)
