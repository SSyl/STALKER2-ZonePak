# Binarized table or plain cfg?

This page shows how to tell whether a SID is in a binarized table or a plain cfg file, and so where its patch goes.

Commands on this page run from the ZonePak folder, as described in [Getting started](Getting-Started.md).

The Zone Kit's cfg files look the same for both kinds. `tables` asks the game which tables it ships binarized and
which files it ships plain:

```
python -m zonepak tables
```

```
Binarized tables (patch with cfg/GameData/<Table>/<any name>.cfg):
  AbilityPrototypes
  AimAssistConePrototypes
  ...

Plain cfg files (patch with cfg/GameData/<File>.cfg_patch_<any name>):
  Achievements.cfg
  AIGlobals.cfg
  ...
```

The full list is about 490 lines, more than the command prompt shows at once. To read it in Notepad, write it to a
file first:

```
python -m zonepak tables > tables.txt
notepad tables.txt
```

`tables` needs only `game` and `repak` from the config file, and no project. `tables --dlc DLC1` lists the Cost of
Hope tables instead, with `cfg/DLCGameData/DLC1/` in the headings.

To place a patch, take the path of the Zone Kit file that defines the SID, relative to `GameData\` and without
`.cfg`, such as `ItemPrototypes\AttachPrototypes`. Read that path from the left one folder at a time, so
`ItemPrototypes` comes first and `ItemPrototypes\AttachPrototypes` second. The table is the first of these that the
binarized list names. For example:

- `ItemPrototypes\AttachPrototypes.cfg` starts with `ItemPrototypes`, a binarized table, so a patch for
  `GunPM_MagDefault` goes in `cfg/GameData/ItemPrototypes/<any name>.cfg`.
- Some binarized tables are nested. `WeaponData\WeaponGeneralSetupPrototypes.cfg` belongs to
  `WeaponData/WeaponGeneralSetupPrototypes`, because the list does not name `WeaponData` alone. Its patches go in
  `cfg/GameData/WeaponData/WeaponGeneralSetupPrototypes/`.
- `CoreVariables.cfg` is in the plain list, so its patch is `cfg/GameData/CoreVariables.cfg_patch_<any name>`.

If you guess wrong, `check` reports an error. A `.cfg` in a folder that is not a binarized table gives
`<Folder> is not a binarized table in the game, so this file is not loaded`. A `.cfg_patch_` file for a binarized
table, such as `cfg/GameData/ItemPrototypes.cfg_patch_MyMod`, gives
`ItemPrototypes.cfg is not a plain table in the game, so this patch is not loaded`.
