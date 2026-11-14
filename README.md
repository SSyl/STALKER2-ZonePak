# ZonePak

ZonePak turns a folder of game-data changes and text changes into a S.T.A.L.K.E.R. 2 mod that you can install in
the game's `~mods` folder or publish on Nexus Mods.

It builds mods in the same layouts as GSC's Zone Kit, the official modding kit. Mods with cfg patches need the
Lesser Zone Kit, which is the Zone Kit's minimal install: the one required component in the Epic Games Launcher's
install options, about 2.25 GB instead of 700 GB+ for the full kit. Text-only mods do not need the Zone Kit. It
checks cfg patches against the vanilla tables, packs cfg-only mods the way the Zone Kit's `PakPlainMod.bat` does,
and builds text-override mods with a generated localization database.

## What ZonePak cannot do

- Build new models, textures, sounds, maps or Blueprints. ZonePak does not cook assets. It builds only cfg patches
  and text.
- Patch data that only the Deluxe, Ultimate and pre-order bonus packs define (`DLCGameData/Deluxe`, `Ultimate` and
  `PreOrder` in the game's paks). Most of their weapons use base-game magazines and upgrades, which a base-game
  patch does reach. See [Patching DLC items](docs/DLC-Items.md).

## Quick start

These steps build the HelloZone example first, so that you can confirm your setup with a mod that is known to
work, and then create a mod of your own. All commands are typed in a Windows command prompt.

### 0. Get ZonePak

Open ZonePak's GitHub page, https://github.com/SSyl/STALKER2-ZonePak, click **Code**, then **Download ZIP**. Extract the zip
and move the extracted folder, which is named like `STALKER2-ZonePak-main`, to `C:\Tools\ZonePak`, so that
`C:\Tools\ZonePak` holds this `README.md` and the `zonepak` folder. Any other folder works too. These docs call it
the ZonePak folder.

### 1. Install the tools

- Python 3.11 or newer. The main Windows download on python.org is now the Python install manager, which these
  docs do not cover. Use the traditional installer instead. Open https://www.python.org/downloads/windows/, pick a
  stable release and download its **Windows installer (64-bit)**. In that installer, tick **Add python.exe to
  PATH**. After any install, open a new command prompt and run `python --version`. If `python` says it is not
  recognized, or opens the Microsoft Store, run `py --version`, and if that works, type `py` in place of `python`
  in every command.
- The Lesser Zone Kit, for mods with cfg patches. GSC distributes the S.T.A.L.K.E.R. 2 Zone Kit on the Epic Games
  Store, so you need a free Epic Games account. When you install the Zone Kit, the Epic Games Launcher shows the
  "S.T.A.L.K.E.R. 2 Zone Kit Installation Options" dialog. Keep "The Lesser Zone kit (Required)" (2.252 GB) ticked,
  and make sure the four optional components, Zone Kit editor, World Map, Pre-renders and Audio via Wwise, are
  unticked.
- `repak.exe` and the patched `retoc.exe`. You do not need to fetch them yourself. The first time a command needs
  one, ZonePak asks whether to download it into its `third_party` folder. Type `y` to download it. ZonePak checks
  the download against a fixed SHA-256 and extracts only the `.exe`. Type `n` to download it yourself instead.
  ZonePak then opens the release page and tells you which file to extract into `third_party`. repak comes from
  https://github.com/trumank/repak/releases and the patched retoc from
  https://github.com/SSyl/STALKER2-zonekit-retoc/releases. Only mods with text need retoc, and HelloZone has text.
  The first time they need Oodle, the tools download its `oo2core_9_win64.dll` next to themselves. To build retoc
  from source, see [Building the patched retoc yourself](docs/Building-Retoc.md).

### 2. Write the config file

Open the ZonePak folder in Explorer, click the address bar, type `cmd` and press Enter. A command prompt opens in
that folder. Run every `python -m zonepak` command from there. Open it only after installing Python, because a
command prompt that was already open does not see the PATH change the Python installer makes.

In the command prompt, create the folder for the config file:

```
mkdir "%APPDATA%\ZonePak"
```

Open Notepad and paste these two lines. Change each path to where the Zone Kit and the game are on your machine.
`zone_kit` is the folder that holds `Stalker2ModEditor.exe`, and `game` is the folder that holds `Stalker2.exe`.
Leave out the `zone_kit` line if you only build text-only mods.

```toml
zone_kit = 'D:\Games\Epic Games\STALKER2ZoneKit'
game = 'D:\Games\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl'
```

If you keep `repak.exe` or `retoc.exe` somewhere other than `third_party`, add a `repak` or `retoc` line with its
path, such as `repak = 'C:\Tools\repak.exe'`.

Keep the single quotes. TOML reads single-quoted strings literally and treats backslashes in double-quoted strings
as escapes.

Choose **File > Save as**. Paste `%APPDATA%\ZonePak` into the dialog's address bar and press Enter, set **Save as
type** to **All files**, and save the file as `config.toml`. Without **All files**, Notepad saves it as
`config.toml.txt` and ZonePak does not find it.

### 3. Build the HelloZone example

HelloZone gives the PM pistol's standard magazine 10 rounds instead of 8 and renames the Bandage in the English
text. The magazine change is a cfg patch, so HelloZone needs the Lesser Zone Kit, and the text needs the patched
`retoc.exe`.

Copy HelloZone out of the ZonePak folder, then check and build the copy:

```
xcopy /E /I examples\HelloZone C:\Mods\HelloZone
python -m zonepak --project C:\Mods\HelloZone check
python -m zonepak --project C:\Mods\HelloZone build
```

If you can't get retoc yet, delete the text file after the `xcopy` and before `check`:

```
del C:\Mods\HelloZone\text\en.toml
```

HelloZone then builds cfg-only, with only the magazine change, and needs no retoc.

`check` prints `0 error(s), 0 warning(s)` and `build` prints `built C:\Mods\HelloZone\build\HelloZone`. The
output is the same with or without the text file. The magazine change was verified in-game on 2026-11-03.
[Getting started](docs/Getting-Started.md) explains each step and how to see the changes in-game.

Options such as `--project` go before the command (`check`, `build` and so on). Always pass `--project`, because
the command prompt is in the ZonePak folder, which is not a mod project.

To install the mod, copy the `C:\Mods\HelloZone\build\HelloZone` folder into
`<game>\Stalker2\Content\Paks\~mods\`. To uninstall it, delete `~mods\HelloZone`.

### 4. Make your own mod

```
python -m zonepak --project C:\Mods new MyMod
```

`new` creates `C:\Mods\MyMod` with a `zonepak.toml`, a fresh database ID, an empty `cfg\GameData\` folder and an
empty `text\` folder. The mod has nothing to build until you add a patch or a text file. As a first patch, give
the PM's extended magazine 14 rounds instead of 12. Create its folder:

```
mkdir C:\Mods\MyMod\cfg\GameData\ItemPrototypes
```

Paste these lines into a new Notepad file and save it as `C:\Mods\MyMod\cfg\GameData\ItemPrototypes\MyMod.cfg`,
again with **Save as type** set to **All files**:

```
GunPM_MagIncreased : struct.begin {bpatch}
   Magazine : struct.begin {bpatch}
      MaxAmmo = 14
   struct.end
struct.end
```

Then check and build it:

```
python -m zonepak --project C:\Mods\MyMod check
python -m zonepak --project C:\Mods\MyMod build
```

`check` reports errors and warnings in the patch files, and errors in the text files. `build` prints the same
findings before building and stops if there are errors. Copy `build\MyMod` into `~mods` to try the mod in game.

Where a patch goes depends on what it changes. [Terms](docs/Terms.md) explains SID, binarized table, plain cfg,
culture and the other words used here.

- Patches for binarized tables go in `cfg/GameData/<Table>/<any name>.cfg`, for example
  `cfg/GameData/ItemPrototypes/MyMod.cfg`.
- Patches for plain cfg files go in `cfg/GameData/<File>.cfg_patch_<any name>`, for example
  `cfg/GameData/CoreVariables.cfg_patch_MyMod`.
- Patches for SIDs that exist only in a DLC go in `cfg/DLCGameData/<DLC>/` by the same rules, for example
  `cfg/DLCGameData/DLC1/ItemPrototypes/MyMod.cfg` for the Cost of Hope expansion. See
  [Patching DLC items](docs/DLC-Items.md).
- Text overrides go in `text/<culture>.toml` as `key = "text"`, for example `text/en.toml`.
  `python -m zonepak text <search>` finds a key by part of the key or of its current text.

`python -m zonepak tables` lists which tables are binarized and which files are plain.
[Binarized table or plain cfg?](docs/Binarized-Table-Or-Plain-Cfg.md) explains how to use that list, and
[Finding SIDs, fields and text keys](docs/Finding-SIDs-And-Text-Keys.md) shows where to look up what to patch.

[Examples](docs/Examples.md) describes the other example projects in `examples/`. For each use case in depth,
see the [documentation index](docs/Home.md). [Troubleshooting](docs/Troubleshooting.md) explains every error and
warning, and the [Reference](docs/Reference.md) lists every config key, flag and `zonepak.toml` field.

## Optional parts

A mod can offer optional parts that players choose in an install wizard when Vortex or Mod Organizer 2 installs it.
Each `[[option]]` table in `zonepak.toml` names a project folder that holds the option's cfg patches, laid out like
the main `cfg/`. `build` packs each option into its own `.pak` and writes the Nexus zip as a FOMOD installer.
`build\<Name>\` holds the main part and the options with `default = true`. Options are cfg-only, and text stays in the
main part. See [Optional parts and FOMOD](docs/Optional-Parts-And-FOMOD.md) and the `examples\Options` project.

```toml
[[option]]
name = "Fora-221: 40-round magazine"
folder = "Fora"            # holds Fora/cfg/GameData/... or Fora/cfg/DLCGameData/...
description = "The Fora-221's standard magazine holds 40 rounds instead of 30."
image = "fomod/fora.png"   # optional, a .png or .jpg in the project
default = true             # optional. true: recommended, ticked in advance, and in build/<Name>/
```

## Todo

- A Steam Workshop workflow. Until then, upload Workshop mods with the Zone Kit.
- Plugin mods, which add content such as a ModWorldSubsystem Blueprint as a game feature plugin. Each one needs an
  asset registry file that ZonePak cannot write yet (`AssetRegistry.bin`, whose name table uses CityHash64
  hashes). Text and cfg-only mods do not need one.
- Publish the pages in `docs/` as the GitHub wiki, so the wiki and the repo never drift apart. The pages are
  already written as wiki pages, and publishing needs a public repo or a paid plan.
- Build-time warning for SIDs that other installed mods in `~mods` also patch.
- Bundle the license notices of the Rust crates compiled into retoc.exe with the release asset.

## Credits

- [ThePsyjo/stalker2-worth-per-weight](https://github.com/ThePsyjo/stalker2-worth-per-weight) for
  the retoc Zone Kit patch and the Zone Kit container and localization database research.
- [trumank/repak](https://github.com/trumank/repak) and [trumank/retoc](https://github.com/trumank/retoc), the pak
  and IoStore tools ZonePak runs.
- [joric/stalker](https://github.com/joric/stalker) for `bin2cfg.py`, which ZonePak ships unchanged to decode the
  game's tables, and the wiki on cfg.bin.
- [sdwvit/S2CfgToJSON](https://github.com/sdwvit/S2CfgToJSON) for cfg patch semantics and Zone Kit config paths.
- [DrBAMF-9091/stalker_2_2.0.5_cfg_dump](https://github.com/DrBAMF-9091/stalker_2_2.0.5_cfg_dump) for patch file
  conventions.
- [rehan-remade/universal-modder](https://github.com/rehan-remade/universal-modder) for Zone Kit layout notes.
- [moritzstrobel/BPRUpgradesExpanded](https://github.com/moritzstrobel/BPRUpgradesExpanded),
  [Zayn995/S2Tweaker](https://github.com/Zayn995/S2Tweaker) and [sdwvit/S2Mods](https://github.com/sdwvit/S2Mods)
  for the DLC patch layout.
- [atenfyr/UAssetAPI](https://github.com/atenfyr/UAssetAPI), the package format reference used to verify the
  localization database writer.
- [GSC's Zone Kit knowledge base](https://zonekit-support.stalker2.com/en-US/kb), especially Config patches
  (KB 145), Mini SDK (KB 148) and Mod TextTool (KB 160).

Licenses for the code ZonePak ships or builds on are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
