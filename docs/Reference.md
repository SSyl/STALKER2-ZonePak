# Reference

This page lists the config file keys and flags, the `zonepak.toml` fields and the files that `build` writes.

## config.toml and flags

The config file is `%APPDATA%\ZonePak\config.toml` unless `--config` names another. A flag overrides the key of the
same name.

| Key | Flag | Used by | Value |
|---|---|---|---|
| `zone_kit` | `--zone-kit` | `check`, `build` | Zone Kit install folder. Vanilla structs are read from `Stalker2\Content\GameLite\GameData`. Only needed for a mod with files under its `cfg/` folders. |
| `game` | `--game` | `check`, `build`, `tables`, `text` | Game install folder. `tables`, and `check` for a mod with files under its `cfg/` folders, list `Stalker2\Content\Paks\pakchunk0-Windows.pak`. `check`, `build` and `text` read the game's text from that pak when a mod has text, or for `text` always. `check` also lists every `<DLC>\*.pak` for the folders under `cfg/DLCGameData/`, and `tables --dlc <DLC>` lists that DLC's. Deluxe, Ultimate and PreOrder have no folder of their own, so for those it lists the main game paks instead. |
| `repak` | `--repak` | `check`, `build`, `tables`, `text` | `repak.exe`. When unset, `third_party\repak.exe`, which ZonePak offers to download. |
| `retoc` | `--retoc` | `build` with text | The patched `retoc.exe`. When unset, `third_party\retoc.exe`, which ZonePak offers to download. |

`--project` is the project folder, and for `new` the folder the project is created in. It defaults to the
current folder. Because you run ZonePak from the ZonePak folder, always pass it. `tables` and `text` ignore it.

`tables` takes its own option, `--dlc <DLC>`, after the command, as in `python -m zonepak tables --dlc DLC1`.

`text <search>` takes `--culture <culture>` (default `en`) and `--limit <n>` (default 50, `0` for all) after the
command. [Text keys](Finding-SIDs-And-Text-Keys.md#text-keys) shows its output.

## zonepak.toml

| Field | Meaning |
|---|---|
| `name` | Required. Letters, digits and underscores. Becomes the mod's folder name in `~mods` and the start of the output file names. |
| `friendly_name` | Display name. Defaults to `name`. For a mod with options, the name in `fomod/info.xml` and the title of the install wizard. Not written into the paks. |
| `description` | For a mod with options, written to `fomod/info.xml`. Not written into the paks. |
| `version` | One to three whole numbers separated by dots, in quotes, such as `"1"`, `"1.0"` or `"1.2.3"`. No leading `v` and no suffix such as `-beta`. Recorded in `build.json` and part of the zip name. Defaults to `1.0`. |
| `database_id` | Required. 10 digits, written by `new`. Names the localization database. |
| `author` | Optional. Text in quotes, such as your name. Recorded in `build.json` when set, and in `fomod/info.xml` for a mod with options. `new` writes it empty. |
| `website` | Optional. Text in quotes, usually the mod's Nexus page. Recorded in `build.json` when set, and in `fomod/info.xml` for a mod with options. `new` writes it empty. |
| `nexus_id` | Optional. The Nexus mod number, the number at the end of the mod's Nexus page address (`.../mods/<number>`). A whole number without quotes, as in `nexus_id = 164`. Recorded in `build.json` when set, and in `fomod/info.xml` as `Id` for a mod with options. |
| `fill_game_text` | Optional. `true` or `false` without quotes, default `false`. For text keys the game has, copies the game's own text into the cultures the text files leave out. The game shows that text there anyway. See [Cultures you leave out](Text-Overrides.md#cultures-you-leave-out). |
| `copy_new_text` | Optional. A culture in quotes, such as `"en"`. For text keys the game does not have, copies that culture's text into the cultures the text files leave out. Off by default. |
| `options_folder` | Optional. A folder name of letters, digits and underscores, in quotes, such as `"options"`. When set, the option folders sit inside it instead of directly in the project folder, as in `options/Fora/cfg/`. Not `cfg`, `text`, `build`, `Main` or `fomod`, in any case. |
| `[[group]]` | Optional, repeatable. One table per group of options, after the fields above. See the group table below. |
| `[[option]]` | Optional, repeatable. One table per option, after the fields above. See the option table below. |

Each `[[group]]` table takes these fields. [Groups](Optional-Parts-And-FOMOD.md#groups) explains them.

| Field | Meaning |
|---|---|
| `name` | Required. Text in quotes. The group's heading in the install wizard. Not `Options`, in any case, and unique among the groups. |
| `select` | Optional. `"one"` makes the player pick exactly one option of the group, and then exactly one of its options needs `default = true`. `"any"`, the default, allows any number. |

Each `[[option]]` table takes these fields. [Optional parts and FOMOD](Optional-Parts-And-FOMOD.md) explains them.

| Field | Meaning |
|---|---|
| `name` | Required. Text in quotes. The option's label in the install wizard. |
| `folder` | Required. Letters, digits and underscores. The folder, in the project folder or in `options_folder` when that is set, that holds the option's `cfg/GameData/` or `cfg/DLCGameData/<DLC>/`, and the option's folder in the zip. Not `cfg`, `text`, `build`, `Main` or `fomod`, in any case, and unique among the options. |
| `description` | Optional. Text in quotes, shown in the wizard. |
| `image` | Optional. The path of a `.png` or `.jpg` file inside the project, from the project folder, such as `"fomod/fora.png"`. Shown in the wizard. |
| `default` | Optional. `true` or `false`, without quotes. Defaults to `false`. `true` makes the option recommended and ticked in advance, and puts its pak in `build/<Name>/`. |
| `group` | Optional. The `name` of a `[[group]]` table, in quotes. Without it, the option is in the `Options` group, where any number can be ticked. |
| `empty` | Optional. `true` or `false`, without quotes. Defaults to `false`. `true` makes the option a wizard choice that installs nothing, with no folder or pak. |

## Output layout

| Path | Contents |
|---|---|
| `build/<Name>/` | The files for `~mods\<Name>\`: the main part and the paks of options with `default = true` |
| `build/<Name>-<version>.zip` | `<Name>/` at the archive root. For a mod with options, `fomod/`, `Main/` and one folder per option, as in [What build writes for a mod with options](Optional-Parts-And-FOMOD.md#what-build-writes-for-a-mod-with-options) |
| `build/build.json` | Versions, database name, `author`, `website` and `nexus_id`, and file hashes |

`build` writes the new build to `build.partial/` next to `build/`, and swaps it in only when everything has
succeeded. If the check, repak or retoc fails, the previous `build/` stays as it was.

| File | Mount point | Contents |
|---|---|---|
| `<Name>Stalker2-Windows-OverrideContent.pak`, cfg-only | `../../../<deepest shared folder>/`, for example `../../../Stalker2/Content/GameLite/GameData/` | The patch files, V11, uncompressed |
| `<Name>_<folder>Stalker2-Windows-OverrideContent.pak`, one per option | `../../../<deepest shared folder>/`, as for a cfg-only pak | The option's patch files, V11, uncompressed |
| `<Name>Stalker2-Windows-OverrideContent.pak`, with text | `../../../Stalker2/Content/GameLite/` | The patch files, or nothing for a text-only mod |
| `<Name>Stalker2-Windows-OverrideContent.utoc` and `.ucas` | `../../../Stalker2/Content/` | `/<Name>/Autogenerated_<database_id>_LocalizationDatabase`, redirected from `/Game/Autogenerated_<database_id>_LocalizationDatabase` |

The mount point is the game folder that the paths inside a `.pak` or `.utoc` start from. The `.utoc` and `.ucas`
form an IoStore container that holds the localization database package, and the `.pak` holds the patch files as
loose files. A cfg-only `.pak` is the same pak `PakPlainMod.bat` makes for the same files. A cfg-only mod with
patches under both `cfg/GameData/` and `cfg/DLCGameData/` mounts at `../../../Stalker2/Content/GameLite/`, and one
with only DLC patches mounts at the deepest folder they share, for example
`../../../Stalker2/Content/GameLite/DLCGameData/DLC1/`. ZonePak makes no
`PakPlainMod.bat` parity claim for DLC files, as [Patching DLC items](DLC-Items.md) explains.
