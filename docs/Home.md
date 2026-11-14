# ZonePak

> [!IMPORTANT]
> ZonePak should be considered alpha and is still under active development. While every effort is made to keep the
> documentation and examples updated, they are bound to get outdated from time to time as development continues.

ZonePak turns a folder of game-data changes and text changes into a S.T.A.L.K.E.R. 2 mod that you can install in
the game's `~mods` folder or publish on Nexus Mods. Start with [Installation](Installation.md) to set up the tools
and config file, then follow [Getting started](Getting-Started.md) to build your first mod.

## Getting started

- [Installation](Installation.md) downloads ZonePak, installs the required tools and writes `config.toml`.
- [Getting started](Getting-Started.md) builds the HelloZone example step by step and starts a mod of your own.
- [Terms](Terms.md) explains SID, binarized table, plain cfg, culture and the other words these pages use.
- [Examples](Examples.md) describes the other example projects and how to check each one in-game.

## How-to

- [Finding SIDs, fields and text keys](Finding-SIDs-And-Text-Keys.md) shows where to look up what to patch.
- [Binarized table or plain cfg?](Binarized-Table-Or-Plain-Cfg.md) shows where a patch file goes.
- [Patching a binarized table](Patching-Binarized-Tables.md) changes fields of existing structs in tables such as
  `ItemPrototypes`.
- [Patching a plain cfg](Patching-Plain-Cfg.md) changes files such as `CoreVariables.cfg`.
- [Adding new structs](New-Structs.md) adds new effects, upgrades and other structs.
- [Patching DLC items](DLC-Items.md) reaches SIDs that only a DLC such as Cost of Hope defines.
- [Text overrides](Text-Overrides.md) replaces the game's text in one or more languages.
- [Generating patches from a script](Generating-Patches.md) builds data-driven mods.
- [Optional parts and FOMOD](Optional-Parts-And-FOMOD.md) offers parts that players choose in Vortex or Mod
  Organizer 2.
- [Publishing](Publishing.md) lists what to upload to Nexus Mods.
- [Building the patched retoc yourself](Building-Retoc.md) builds `retoc.exe` from source.

## Reference

- [Reference](Reference.md) lists the config file keys, flags, `zonepak.toml` fields and output files.

## Help

- [Troubleshooting](Troubleshooting.md) explains every error and warning, and what to check when a mod changes
  nothing in-game.

## About these pages

These pages are written in the repo's `docs` folder and published to the wiki from there, so edits made on the wiki
are overwritten.
