# ZonePak

> [!IMPORTANT]
> ZonePak should be considered alpha and is still under active development. While every effort is made to keep the
> documentation and examples updated, they are bound to get outdated from time to time as development continues.

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
  patch does reach. See [Patching DLC items](https://github.com/SSyl/STALKER2-ZonePak/wiki/DLC-Items).

## Quick start

1. **Install prerequisites:** Python 3.11+ (with `python` on `PATH`) and, for cfg mods, the Lesser Zone Kit from the
   Epic Games Store. `repak.exe` and the patched `retoc.exe` download automatically on first use. See
   [Installation](https://github.com/SSyl/STALKER2-ZonePak/wiki/Installation) for step-by-step setup.
2. **Create `%APPDATA%\ZonePak\config.toml`** pointing to your Zone Kit and game folders:

   ```toml
   zone_kit = 'D:\Games\Epic Games\STALKER2ZoneKit'
   game = 'D:\Games\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl'
   ```

3. **Build the HelloZone example** from the ZonePak folder:

   ```
   xcopy /E /I examples\HelloZone C:\Mods\HelloZone
   python -m zonepak --project C:\Mods\HelloZone check
   python -m zonepak --project C:\Mods\HelloZone build
   ```

   Copy `C:\Mods\HelloZone\build\HelloZone` into `<game>\Stalker2\Content\Paks\~mods\` to try it in-game.

See [Getting started](https://github.com/SSyl/STALKER2-ZonePak/wiki/Getting-Started) for a full walkthrough and how to
create your own mod.

## Documentation

Full guides and references live on the **[ZonePak Wiki](https://github.com/SSyl/STALKER2-ZonePak/wiki)**:

- [Installation](https://github.com/SSyl/STALKER2-ZonePak/wiki/Installation) and
  [Getting started](https://github.com/SSyl/STALKER2-ZonePak/wiki/Getting-Started)
- [Terms](https://github.com/SSyl/STALKER2-ZonePak/wiki/Terms) and
  [Examples](https://github.com/SSyl/STALKER2-ZonePak/wiki/Examples)
- [Patching binarized tables](https://github.com/SSyl/STALKER2-ZonePak/wiki/Patching-Binarized-Tables),
  [plain cfgs](https://github.com/SSyl/STALKER2-ZonePak/wiki/Patching-Plain-Cfg),
  [DLC items](https://github.com/SSyl/STALKER2-ZonePak/wiki/DLC-Items), and
  [text overrides](https://github.com/SSyl/STALKER2-ZonePak/wiki/Text-Overrides)
- [Optional parts and FOMOD](https://github.com/SSyl/STALKER2-ZonePak/wiki/Optional-Parts-And-FOMOD) and
  [Publishing](https://github.com/SSyl/STALKER2-ZonePak/wiki/Publishing)
- [Reference](https://github.com/SSyl/STALKER2-ZonePak/wiki/Reference) and
  [Troubleshooting](https://github.com/SSyl/STALKER2-ZonePak/wiki/Troubleshooting)

## Todo

- A Steam Workshop workflow. Until then, upload Workshop mods with the Zone Kit.
- Plugin mods, which add content such as a ModWorldSubsystem Blueprint as a game feature plugin. Each one needs an
  asset registry file that ZonePak cannot write yet (`AssetRegistry.bin`, whose name table uses CityHash64
  hashes). Text and cfg-only mods do not need one.
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
