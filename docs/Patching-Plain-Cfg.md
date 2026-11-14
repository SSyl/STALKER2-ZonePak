# Patching a plain cfg

This page covers patching the GameData files that the game ships as plain `.cfg` text, such as
`CoreVariables.cfg`. `python -m zonepak tables` lists them.

Commands on this page run from the ZonePak folder, as described in [Getting started](Getting-Started.md).

Patch one with a file next to its path, named `cfg/GameData/<File>.cfg_patch_<any name>`:

```
cfg/GameData/CoreVariables.cfg_patch_MyMod
```

```
DefaultConfig : struct.begin {bpatch}
   CorpseTimeout = 3000
struct.end
```

For a plain file in a subfolder, keep the subfolder: `cfg/GameData/<Folder>/<File>.cfg_patch_<any name>`. The game
does not read `.cfg_patch_` files inside a binarized table's folder, and `check` reports an error for them. The
commands and output are the same as for [a binarized table](Patching-Binarized-Tables.md).

A whole edited copy of a plain file at its own path, such as `cfg/GameData/CoreVariables.cfg`, replaces the vanilla
file. This was verified in-game on 2026-11-03. `check` warns about it and does not check its contents, and `build`
packs it. The warning is there because only one mod can replace a file, other mods' patches cannot apply to it, and
later game updates to that file are hidden. A `.cfg_patch_` file is the better choice unless you need to change
most of the file.
