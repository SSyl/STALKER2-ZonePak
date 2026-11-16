# Patching DLC items

This page covers patching SIDs that a DLC defines, and what ZonePak can and cannot reach in the DLCs.

Commands on this page run from the ZonePak folder, as described in [Getting started](Getting-Started.md).

SIDs that exist only in a DLC's own tables are patched under `cfg/DLCGameData/<DLC>/`, because a patch under
`cfg/GameData/` does not reach them. `<DLC>` is the DLC's folder name in the game install. The Cost of Hope
expansion is `DLC1` (`<game>\DLC1\S2_DLC1Stalker2-Windows.pak`). Inside a DLC folder the placement rules are the
same as under `cfg/GameData/`, and `python -m zonepak tables --dlc DLC1` lists its tables:

```
cfg/DLCGameData/DLC1/ItemPrototypes/MyMod.cfg
cfg/DLCGameData/DLC1/NPCNames.cfg_patch_MyMod
```

The Deluxe, Ultimate and pre-order bonus items are not in a DLC folder. Their own data sits under
`DLCGameData/Deluxe`, `Ultimate` and `PreOrder` inside the main game paks (`pakchunk102`, `pakchunk104` and
`pakchunk101`). Patch those SIDs under `cfg/DLCGameData/Deluxe/`, `Ultimate/` or `PreOrder/`, spelled with that case.
When a folder name under `cfg/DLCGameData/` has no game folder, `check` reads its table list from the main game paks,
and `tables --dlc Deluxe` lists it. Most of these weapons use base-game magazines and upgrades, so a patch under
`cfg/GameData/` reaches those, but their weapon setups (upgrade trees) exist only in these folders. Published mods
such as Customizable Unique Weapons replace `DLCGameData/Deluxe/WeaponGeneralSetupPrototypes.cfg` wholesale. A
`{bpatch}` under these folders has not been checked in game yet.

`check` reads the DLC's table list from every `.pak` in `<game>\<DLC>\`, and reports an error for files that
match no DLC table the same way it does for `GameData`. So `check` and `build` need the DLC installed on the
machine that builds the mod, even for the mod's base-game patches. Players without the DLC can still use the mod.

Neither the lesser nor the full Zone Kit has DLC cfg data, so `check` cannot compare a DLC patch with vanilla. It still reports
syntax errors, and warns once for each root struct:

```
DLCGameData/DLC1/ItemPrototypes/MyMod.cfg:1: warning: <SID> not checked: the Zone Kit has no DLC1 data
```

Check the SIDs and field names against the DLC's own tables yourself. When a `{bpatch}` SID under `cfg/GameData/`
does not exist in vanilla, the error ends with a hint to move the patch under `cfg/DLCGameData/<DLC>/` if the SID
is a DLC item.

`build` packs the DLC patches into the same `.pak` as the rest.

- The path `Stalker2/Content/GameLite/DLCGameData/DLC1/<Table>/<file>.cfg` with `{bpatch}` follows published mods
  that patch Cost of Hope SIDs, such as BPR Upgrades Expanded, S2Tweaker and sdwvit's S2Mods. It was verified
  in-game on 2026-11-03 with a ZonePak build that held base-game and Cost of Hope patches in one pak: a magazine
  that exists only in Cost of Hope took its new capacity, and a Cost of Hope weapon took a hidden upgrade defined
  in the base tables. The same pak also works on a copy without Cost of Hope: the game loads, the base-game
  patches apply, and the Cost of Hope patches do nothing. One pak per mod is enough, and DLC patches do not need
  a separate download.
- ZonePak packs these files with repak itself. The Zone Kit's mod cook settings
  (`Stalker2/Config/Custom/ModCookOverrideContent/DefaultGame.ini`) remove the `GameLite/DLCGameData/*` folders
  from the always-stage list, which suggests `PakPlainMod.bat` would leave them out. Nobody has tested that, so
  ZonePak makes no parity claim for DLC files.
