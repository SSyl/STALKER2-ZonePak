# Troubleshooting

This page lists ZonePak's error and warning messages with their meaning and fix, and what to check when an
installed mod changes nothing in-game.

## Running ZonePak

| Message | Meaning and fix |
|---|---|
| `'python' is not recognized as an internal or external command, operable program or batch file.` | Python is not on PATH in this command prompt. A prompt that was open while Python was installing does not see the new PATH, so first close it and open a new one in the ZonePak folder. If that does not help, type `py` in place of `python`, or reinstall Python with **Add python.exe to PATH** ticked. |
| `<path>\python.exe: No module named zonepak` | The command prompt is not in the ZonePak folder. Open it there as in step 2 of [Installation](Installation.md#2-write-the-config-file), or run `cd /d C:\Tools\ZonePak` with your ZonePak folder first. |
| `zonepak: error: unrecognized arguments: --project C:\Mods\MyMod`, after a `usage:` line | A global option came after the command. Put `--project` and the other global options before `check`, `build`, `tables` or `text`, as in `python -m zonepak --project C:\Mods\MyMod check`. |

## check errors and warnings

Each finding prints as `<file>:<line>: <level>: <message>`, where `<file>` is relative to `cfg/` and line 0 means
the whole file. A file of an option prints relative to the project folder, as `<folder>/cfg/...`. A text file
prints as `text/<culture>.toml`, always with line 0, and a TOML error names its line in the message. `check` stops
at the first broken text file. Errors stop `build`. Warnings do not. A misplaced `.cfg` or `.cfg_patch_*` file,
which the game would not load, is an error, so it stops the build instead of shipping a mod that does nothing. Any
other file under `cfg/` gets a warning, because `build` never packs it. A name ending in `.cfg.txt` is an error,
because it is usually a patch that Notepad saved as a text file.

| Message | Level | Meaning and fix |
|---|---|---|
| `<SID> does not exist in <Table>. If it is a DLC item, put the patch under cfg/DLCGameData/<DLC>/.` | error | A `{bpatch}` root names a SID the table lacks. Check the spelling, or that the file is in the right table folder. A SID that exists only in a DLC goes under `cfg/DLCGameData/<DLC>/`, as in [Patching DLC items](DLC-Items.md). A `{bpatch}` may also name a new struct of its own part, or an option's may name one of the main part's, and `check` does not check its fields. |
| `<SID>.<path> does not exist in vanilla` | error | The field or nested struct is neither defined nor inherited by that SID. Check the spelling against the vanilla file, as in [SIDs and fields](Finding-SIDs-And-Text-Keys.md#sids-and-fields). |
| `<SID>.<path> is a value in vanilla, not a struct` | error | The patch opens a struct where vanilla has a plain value. |
| `<SID>.<path> is a struct in vanilla, not a value` | error | The patch assigns a value where vanilla has a struct. Open the struct with `{bpatch}` and patch the field inside. |
| `refkey <SID> does not exist in <Table>` | error | A new struct's `refkey` names nothing in the same table, vanilla or the mod's own files. An option's struct can name a new struct of its own option or of the main part, but not of another option. A struct in the main part cannot name an option's new struct. |
| `unrecognized line: <text>` | error | The line is not `struct.begin`, `struct.end`, `key = value` or `removenode`. |
| `struct.end without a matching struct.begin` | error | Remove the extra `struct.end`. |
| `struct.begin for <name> is never closed` | error | Add the missing `struct.end`. |
| `not UTF-8 text` | error | Save the file as UTF-8. |
| `unknown culture '<culture>'. Use one of: ...` | error | A `text/` file is not named after a culture. Rename it to one of the 18 culture codes. |
| `<key> must be a string. Quote keys that contain dots.` | error | Quote the key, as in `"a.b" = "text"`. |
| `empty key` | error | Remove the `"" = ...` line from the text file. |
| `<TOML error>`, for example `Illegal character '\n' (at line 1, column 20)` | error | The text file is not valid TOML. The example is a string with no closing quote. |
| `outside GameData and DLCGameData/<DLC>, so the game does not load it as a patch` | error | Move the file under `cfg/GameData/`, or under `cfg/DLCGameData/<DLC>/` for a DLC table. |
| `replaces the whole vanilla <File>.cfg, so other mods cannot patch it and game updates to it are hidden. A <File>.cfg_patch_<name> file changes only what it lists` | warning | The file is a full copy of a plain cfg at its vanilla path. `build` packs it, and it replaces the vanilla file. `check` does not check its contents, so syntax errors in it are not reported. Rename it to `<File>.cfg_patch_<name>` and keep only the changed structs, unless you mean to replace the whole file. |
| `<Folder> is not a binarized table in the game, so this file is not loaded` | error | The `.cfg` is in a folder that is not a binarized table. Use a folder that `python -m zonepak tables` lists under Binarized tables, or `tables --dlc <DLC>` for a DLC patch. A `.cfg` directly in `cfg/GameData/` needs a table folder, such as `cfg/GameData/ItemPrototypes/`. See [Binarized table or plain cfg?](Binarized-Table-Or-Plain-Cfg.md). |
| `<File>.cfg is not a plain table in the game, so this patch is not loaded` | error | The `.cfg_patch_` file names a plain cfg the game does not ship. Check the name and folder against the Plain cfg files list of `python -m zonepak tables`. A binarized table takes a `.cfg` in its folder instead. |
| `plain-cfg patches are not read inside a binarized table folder (<Table>), so this file is not loaded` | error | Rename it to `.cfg`, or move it next to the plain file it patches. |
| `Notepad saved this file as a text file. Rename it to end in .cfg instead of .cfg.txt` | error | The file name ends in `.cfg.txt`, so `build` would leave it out. Rename it, for example from `MyMod.cfg.txt` to `MyMod.cfg`. In Notepad, set **Save as type** to **All files** when you save a patch. |
| `not a .cfg or .cfg_patch_ file, so build does not pack it` | warning | The file, such as `notes.txt`, cannot change the mod. Move it out of `cfg/` to silence the warning. `check` ignores files the system or other tools leave there: `Thumbs.db`, `desktop.ini`, `.DS_Store` and names that start with a dot, such as `.gitkeep`. |
| `<SID> not checked: the Zone Kit has no <DLC> data` | warning | Expected for every root struct in a DLC patch file. Check the SID and fields against the DLC's tables yourself. |
| `<n> SID(s) inherit <fields> from <SID> through refkey and may not get this patch: <SIDs>. Patch them too if they should change` | warning | The listed SIDs get those fields from the patched SID through `refkey`. In the binarized tables tested so far, a patch on the parent did not reach them. Patch each listed SID too, or ignore the warning if they should keep vanilla values. Only SIDs in the Zone Kit's base-game data are listed. See [Patching a binarized table](Patching-Binarized-Tables.md). |
| `<SID> has no {bpatch} and replaces the whole vanilla struct` | warning | Add `{bpatch}` unless replacing the struct is intended. |
| `<SID>.<path> is also set by the main part's <File>.cfg. The game uses the patch file whose name sorts last, so the main part's value wins. Give this file a name that sorts after <File>.cfg` | warning | An option's patch file sorts before the main part's file in the same table folder, and both set that field. Rename the option's file, for example from `MyMod-Fora.cfg` to `MyMod_Fora.cfg`. See [Optional parts](Optional-Parts-And-FOMOD.md). |
| `removenode on <SID>.<path>, which does not exist` | warning | Nothing to remove. Check the spelling. |
| `no patch files under <folder>/cfg/GameData/ or <folder>/cfg/DLCGameData/<DLC>/, so the option installs nothing. Add empty = true if that is intended` | error | An `[[option]]` names a folder that is missing, empty, or holds no `.cfg` or `.cfg_patch_*` file in a place `build` packs. Check that `folder` matches the folder's name and that the patches are under its `cfg/GameData/` or `cfg/DLCGameData/<DLC>/`. For a choice that installs nothing on purpose, add `empty = true`. |
| `the option has empty = true, so build leaves out its patch files. Remove empty = true, or the files` | error | An option marked `empty = true` has patch files in its folder. |
| `has the same game path as <other file>, so the game loads only one of them` | warning | Two parts of the mod, the main part and an option or two options, hold a patch file at the same path under `GameData/` or `DLCGameData/<DLC>/`, compared without case. Each part is its own pak, so when both are installed the game reads only one of the two files. This follows how Unreal Engine paks override each other and has not been tested in this game. Rename one of the files, for example to `MyMod_Fora.cfg`. |
| `<key> is not one of the game's text keys and has no text for <n> culture(s) (<cultures>), so players using those languages see the raw key. If it is a new key, add their texts or set copy_new_text = "<culture>" in zonepak.toml. If not, check its spelling with "zonepak text"` | warning | A text file names a key that the game's own text does not have, and `build` leaves the listed cultures without a text. If the key is new on purpose, add texts for those cultures or set `copy_new_text`. Otherwise find the right key with `python -m zonepak text`. See [Cultures you leave out](Text-Overrides.md#cultures-you-leave-out). |
| `top-level line outside any struct` | warning | A line sits outside every struct, and `check` does not validate it. Some plain cfg files have values at the top level in vanilla, such as `CoreVariables.cfg` and `SettingsVariablesPC.cfg`, and a patch line for one of those values belongs at the top level too. Otherwise the line probably belongs inside a struct, so move it into the struct it patches. |

## Build errors

| Message | Meaning and fix |
|---|---|
| `<n> error(s) in patch or text files` | `build` found check errors, printed above it. Fix them and build again. |
| `nothing to build: no patch files under cfg/GameData/ or cfg/DLCGameData/ and no text/*.toml entries` | Add patches or text. |
| `nothing to build: no patch files under cfg/GameData/ or cfg/DLCGameData/ and no text/*.toml entries. Options cannot be the whole mod, so the main part needs patches or text too` | The mod has options, but its main `cfg/` and `text/` are empty. Move the changes every player needs into the main part. |
| `retoc wrote no package redirect. Set retoc to the patched build from STALKER2-zonekit-retoc.` | `retoc` is a stock build. Remove the `retoc` line from the config file so that ZonePak offers to download the patched one, or build it as in [Building the patched retoc yourself](Building-Retoc.md). |
| `cannot run <path>: ...` | The `repak` or `retoc` path is wrong. If the path in the message contains odd characters, a double-quoted path in the config turned `\t` or `\r` into a tab or line break. Use single quotes. |
| `<game>\Stalker2\Content\Paks\pakchunk0-Windows.pak not found. Is game set to the folder that holds Stalker2.exe?` | The `game` path in the config file, or `--game`, is not the game's install folder. Set it to the folder that holds `Stalker2.exe`, such as `D:\Games\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl`. |
| `repak.exe <command> failed (<code>): <repak output>`, for example `repak.exe list failed (1): ...` | repak ran but stopped with an error. The text after the colon is repak's own message. |
| `retoc.exe to-zen failed (<code>): <retoc output>` | retoc ran but stopped with an error while `build` converted the text. The text after the colon is retoc's own message. Check that `retoc` is the patched build. |

## Built and installed, but nothing changed in-game

You copied the build into `~mods`, but the game shows no change. Go through these checks:

- Open `<game>\Stalker2\Content\Paks\~mods\<Name>\`. A cfg-only mod has one file there,
  `<Name>Stalker2-Windows-OverrideContent.pak`. A mod with text has three, the `.pak`, `.ucas` and `.utoc`. Each
  option with `default = true` adds its own `.pak`. If the folder is missing, check that `game` in the config file is
  the game you start.
- A magazine that was loaded before the mod was installed may keep its old capacity until it is unloaded and
  reloaded.
- A gun spawned from the console shows the vanilla magazine capacity in its tooltip until its first reload, then the
  modded one (seen in-game on 2026-11-04).
- Text overrides show only when the game language is set to a culture the mod has a `text/<culture>.toml` for.
- Another mod in `~mods` may patch the same SID. ZonePak does not warn about that yet, so move the other mod out of
  `~mods` and test again.
- Patches under `cfg/DLCGameData/<DLC>/` change nothing unless that DLC is installed in the game.
- If another mod ships a whole copy of a plain cfg, such as `CoreVariables.cfg`, it replaces the vanilla file, and
  your `.cfg_patch_` for that file cannot apply to it. See [Patching a plain cfg](Patching-Plain-Cfg.md).

## Config and project errors

| Message | Meaning and fix |
|---|---|
| `<key> is not set and <ZonePak>\third_party\<key>.exe does not exist. Download ...` | ZonePak needs repak or retoc but cannot ask whether to download it, because it is not running in a command prompt, for example when a script starts it. Follow the steps in the message, or run the same command once in a command prompt and type `y`. |
| `<url> has SHA-256 <hash>, expected <hash>. Nothing was written.` | The downloaded file differs from the release ZonePak expects. Try again later, or download the file yourself and compare it with the release page. |
| `cannot download <url>: <error>` | The download failed, for example without an internet connection. Type `n` at the question and download the file yourself, as the message after it explains. |
| `<key> is not set, and the config file <config file> does not exist yet. Create it as step 2 of the README quick start shows, or pass --<key>.` | ZonePak found no config file. Write `%APPDATA%\ZonePak\config.toml` as the README's step 2 describes. If you saved it from Notepad, check that it is not named `config.toml.txt`. |
| `<key> is not set. Add it to <config file> or pass --<key>.` | The command needs that key. Add it to the config file, or pass the flag, which spells the key with a hyphen, as in `--zone-kit` for `zone_kit`. If the key is in your config file, check that Notepad did not save the file as `config.toml.txt`. |
| `<zone_kit>\Stalker2\Content\GameLite\GameData not found. Is zone_kit set to the Zone Kit install folder?` | `zone_kit` must be the folder that holds `Stalker2ModEditor.exe`, such as `D:\Games\Epic Games\STALKER2ZoneKit`. |
| `Zone Kit: not usable. <reason>` | Printed first by `check` and `build`. The reason is one of the errors in this table. A text-only mod still builds, and a mod with cfg patches stops with the same error. |
| `zone_kit_mode must be one of none, lesser, full` | The config file sets `zone_kit_mode` to something else. Spell it in lowercase, or remove the line to use the Zone Kit ZonePak finds. |
| `zone_kit_mode = <mode>, but <zone_kit> is the <level> Zone Kit. zone_kit_mode can only lower the level ZonePak detects, ...` | `zone_kit_mode` asks for more than is installed. Remove the line, or set it to the level named or lower. With `zone_kit is not set` instead of a folder, add a `zone_kit` line too. |
| `Checking cfg patches needs the lesser Zone Kit or higher, and zone_kit_mode = none keeps ZonePak from using <zone_kit>` | `zone_kit_mode = 'none'` makes ZonePak work without the Zone Kit, which cannot check cfg patches yet. Remove the line or set it to `lesser`. |
| `<path> not found` | The file given with `--config` does not exist. |
| `<DLC> is not a DLC folder in the game install (no <game>\<DLC>\*.pak)` | A folder under `cfg/DLCGameData/` has no matching folder with a `.pak` in the game install. Rename it to the DLC's folder name, for example `DLC1` for Cost of Hope, or the DLC is not installed on this machine. Building DLC patches needs the DLC installed, even though players without it can use the mod. Until then this error stops `check` and `build` for the whole mod, base-game patches included. |
| `DLC folder '<folder>' must be spelled <DLC>, like the game folder` | A folder under `cfg/DLCGameData/`, or the `tables --dlc` value, differs from the game's DLC folder only in case, for example `dlc1`. The game's pak paths are case-sensitive, so rename the folder, or pass `--dlc` spelled like the game folder. |
| `<path>: unknown keys <keys>` | The config file or `zonepak.toml` has a misspelled key. |
| `<path>: <key> must be a path string` | A config value is empty or not a string. |
| `<path>: <TOML error>`, for example ``config.toml: Unescaped '\' in a string (at line 1, column 14)`` | The config file or `zonepak.toml` is not valid TOML. The usual cause is a double-quoted Windows path such as `"C:\Tools\retoc.exe"`. Use single quotes, as in `'C:\Tools\retoc.exe'`. |
| ``<path>\zonepak.toml not found. Run `python -m zonepak --project <parent folder> new <Name>` to create a project.`` | `--project` does not point at a project folder. Without `--project`, ZonePak looks in the current folder, which is the ZonePak folder. |
| `<path>: database_id must be 10 digits` | Restore the ID `new` wrote. |
| `<path>: version must be one to three numbers separated by dots, in quotes, for example "1.0"` | `version` in `zonepak.toml` has a `v`, a suffix such as `-beta`, more than three numbers, or no quotes. Write it as `version = "1.2"`. |
| `<path>: nexus_id must be a whole number above 0, the number in the mod's Nexus URL` | `nexus_id` is in quotes, has a decimal point, or is 0 or less. Write it as `nexus_id = 164`, with the number from the mod's Nexus page address. |
| `<path>: <key> must be text in quotes` | `author` or `website` in `zonepak.toml` is a number or another value without quotes. Put it in quotes, as in `author = "Your Name"`. |
| `<path>: <key> contains a control character (U+<code>) that the FOMOD files cannot hold. In double quotes, a backslash starts an escape such as \f. Use single quotes, or write \\ for each backslash` | `friendly_name`, `description`, `author` or `website` in `zonepak.toml` holds a character that an XML file cannot contain, here the one with code `<code>`. ZonePak writes these fields into the FOMOD files, so it rejects them for every mod. The usual cause is a Windows path in double quotes, such as `"see ~mods\folder"`, where TOML reads `\f` as a form feed (U+000C). Use single quotes, as in `'see ~mods\folder'`, or double each backslash, as in `"see ~mods\\folder"`. The same message with `a character` in place of `a control character` names U+FFFE or U+FFFF, which XML does not allow either. |
| `mod name '<name>' must use only letters, digits and underscores` | Pick another name. |
| `mod name '<name>' is reserved, because ZonePak uses build/<name>/ itself` | `stage`, in any case, is taken. Pick another name. |
| `<path> already exists` | `new` will not overwrite a folder. |

In the option errors below, `option <n>` counts the `[[option]]` tables from the top of `zonepak.toml`, starting at
1.

| Message | Meaning and fix |
|---|---|
| `<path>: write each option as a table that starts with [[option]]` | `zonepak.toml` has `[option]` with single brackets, or an `option = ...` line. Start each option with `[[option]]`, as in [Optional parts and FOMOD](Optional-Parts-And-FOMOD.md). |
| `<path>: option <n>: unknown keys <keys>` | An option has a misspelled key. Options take `name`, `folder`, `description`, `image`, `default`, `group` and `empty`. |
| `<path>: option <n>: group must be the name of a [[group]] table, in quotes` | The option's `group` names no declared group. Check the spelling against the group's `name`, or add the `[[group]]` table. |
| `<path>: option <n>: name is required, as text in quotes` | Add `name = "..."` to the option, with some text in the quotes. |
| `<path>: option <n>: folder is required and must use only letters, digits and underscores` | Add `folder = "..."`, or rename the folder, for example from `Cost of Hope` to `CostOfHope`. |
| `<path>: option <n>: folder '<folder>' is reserved. cfg, text, build, Main and fomod, in any case, are taken` | Pick another folder name. ZonePak uses these for the main part, the build and the FOMOD zip. |
| `<path>: option <n>: folder '<folder>' is already used by option <m>` | Two options name the same folder, compared without case. Give each option its own folder. |
| `<path>: option <n>: description must be text in quotes` | Put the description in quotes. |
| `<path>: option <n>: <key> contains a control character (U+<code>) that the FOMOD files cannot hold. In double quotes, a backslash starts an escape such as \f. Use single quotes, or write \\ for each backslash` | The option's `name`, `description` or `image` holds a character that `ModuleConfig.xml` cannot contain. Fix it as for the same message without `option <n>` above. |
| `<path>: option <n>: default must be true or false, without quotes` | Write `default = true` or `default = false`, not `default = "true"`. |
| `<path>: option <n>: image must be the path of a .png or .jpg file, in quotes` | Convert the image to PNG or JPEG, or fix the file extension. |
| `<path>: option <n>: image must be a path inside the project folder, such as "fomod/option.png"` | The path is absolute or uses `..`. Copy the image into the project, for example into a `fomod/` folder, and give its path from the project folder. |
| `<path>: option <n>: image <path> not found` | Check the spelling, and that the path starts from the project folder. |
| `<path>: option <n>: image file name <file> is already used by the image of option <m>. Rename one of the two files` | All images share `fomod/images/` in the zip, so two different images need different file names. |
| `<path>: option <n>: options are cfg-only, so <folder>/text/ is not allowed. Put text in the main part's text/ folder` | Move the text into the main `text/` folder. Options cannot carry text. |

In the group errors below, `group <n>` counts the `[[group]]` tables from the top of `zonepak.toml`, starting at 1.

| Message | Meaning and fix |
|---|---|
| `<path>: write each group as a table that starts with [[group]]` | `zonepak.toml` has `[group]` with single brackets, or a `group = ...` line outside an option. Start each group with `[[group]]`, as in [Groups](Optional-Parts-And-FOMOD.md#groups). |
| `<path>: group <n>: unknown keys <keys>` | A group has a misspelled key. Groups take `name` and `select`. |
| `<path>: group <n>: name is required, as text in quotes` | Add `name = "..."` to the group. |
| `<path>: group <n>: name '<name>' is reserved for options without a group` | `Options` is taken in any case. Pick another name. |
| `<path>: group <n>: name '<name>' is already used by group <m>` | Two groups share a name, compared without case. Rename one. |
| `<path>: group <n>: select must be "any" or "one"` | Write `select = "one"` or `select = "any"`, in quotes. |
| `<path>: group '<name>' has no options` | No option names this group in its `group` key. Add options to it or remove the group. |
| `<path>: group '<name>' has select = "one", so exactly one of its options needs default = true` | Set `default = true` on exactly one of the group's options, the one `build/<Name>/` holds and the mod managers pick by default. |
