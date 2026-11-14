# Installation

These steps download ZonePak, install the required tools and create the config file. All commands are typed in a
Windows command prompt.

## 0. Get ZonePak

Open ZonePak's [GitHub page](https://github.com/SSyl/STALKER2-ZonePak), click **Code**, then **Download ZIP**. Extract
the zip and move the extracted folder, which is named like `STALKER2-ZonePak-main`, to `C:\Tools\ZonePak`, so that
`C:\Tools\ZonePak` holds `README.md` and the `zonepak` folder. Any other folder works too. These docs call it the
ZonePak folder.

## 1. Install the tools

- **Python 3.11 or newer.** The main Windows download on python.org is now the Python install manager, which these
  docs do not cover. Use the traditional installer instead. Open
  [python.org/downloads/windows](https://www.python.org/downloads/windows/), pick a stable release and download its
  **Windows installer (64-bit)**. In that installer, tick **Add python.exe to PATH**. After any install, open a new
  command prompt and run `python --version`. If `python` says it is not recognized, or opens the Microsoft Store, run
  `py --version`, and if that works, type `py` in place of `python` in every command.
- **The Lesser Zone Kit**, for mods with cfg patches. GSC distributes the S.T.A.L.K.E.R. 2 Zone Kit on the Epic Games
  Store, so you need a free Epic Games account. When you install the Zone Kit, the Epic Games Launcher shows the
  "S.T.A.L.K.E.R. 2 Zone Kit Installation Options" dialog. Keep "The Lesser Zone kit (Required)" (2.252 GB) ticked,
  and make sure the four optional components, Zone Kit editor, World Map, Pre-renders and Audio via Wwise, are
  unticked.
- **`repak.exe` and the patched `retoc.exe`.** You do not need to fetch them yourself. The first time a command needs
  one, ZonePak asks whether to download it into its `third_party` folder. Type `y` to download it. ZonePak checks
  the download against a fixed SHA-256 and extracts only the `.exe`. Type `n` to download it yourself instead.
  ZonePak then opens the release page and tells you which file to extract into `third_party`. `repak` comes from
  [trumank/repak](https://github.com/trumank/repak/releases) and the patched `retoc` from
  [SSyl/STALKER2-zonekit-retoc](https://github.com/SSyl/STALKER2-zonekit-retoc/releases). Only mods with text need
  retoc. The first time they need Oodle, the tools download its `oo2core_9_win64.dll` next to themselves. To build
  retoc from source, see [Building the patched retoc yourself](Building-Retoc.md).

## 2. Write the config file

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

Next: [Getting started](Getting-Started.md) builds the HelloZone example step by step and starts a mod of your own.
