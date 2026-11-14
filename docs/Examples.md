# Examples

This page describes the example projects in the
[examples folder](https://github.com/SSyl/STALKER2-ZonePak/tree/main/examples) other than HelloZone, which
[Getting started](Getting-Started.md) covers. They check and build the same way as HelloZone. Each has
its own fixed `database_id`, because `zonepak.toml` requires one even for a mod without text.

## SteadyBarrel

Do not install SteadyBarrel together with HelloZone. Both change the PM's standard magazine, which would then
hold 10 x 1.25 = 12.5 rounds, and how the game rounds 12.5 is unverified.

`examples\SteadyBarrel` adds a new effect and appends it to a vanilla upgrade by array index.
`cfg/GameData/EffectPrototypes/SteadyBarrel.cfg` defines `SteadyBarrel_AmmoCapacity25`, a new root struct
without `{bpatch}` that inherits vanilla `AmmoCapacityIncrease1` (type `AmmoCapacity`, permanent) through
`refkey` and sets `ValueMin` and `ValueMax` to `25%`. `cfg/GameData/UpgradePrototypes/SteadyBarrel.cfg` adds it
to the PM's first barrel upgrade, `GunPM_Upgrade_Barrel_1`, as `EffectPrototypeSIDs` item `[1]`, after vanilla's
`[0] = ProjectileSpeedPos20Effect`. That upgrade has no prerequisites.

To check it in-game, buy the upgrade for a PM at a technician. The standard magazine should then hold 10 rounds
instead of 8 and the extended magazine 15 instead of 12. The game rounds the scaled capacity to the nearest
round.

SteadyBarrel itself is not yet verified in-game. Appending an `AmmoCapacity` effect by index was verified in-game
on 2026-11-02. In a test mod that set the UDP's magazines to 12 and 17 rounds, a -25% effect appended to
`GunUDP_Upgrade_Barrel_1` gave 9 and 13. In the same tests, a +25% effect on a 17-round magazine gave 21. 12.75
became 13 and 21.25 became 21, so the game rounds to the nearest round, neither always up nor always down. A
`refkey` from a patch file to a vanilla effect follows GSC's KB 145 but is not yet verified in-game.

## CoreTweak

`examples\CoreTweak` patches a plain cfg. Its one file, `cfg/GameData/CoreVariables.cfg_patch_CoreTweak`, sets
`BinocularsMagnificationMultiplier` in `DefaultConfig` from 1.0 to 2.0. The comment above that value in vanilla
`CoreVariables.cfg` says it scales the whole magnification range, minimum zoom included, so that 1x to 4x becomes
2x to 8x at 2.0. To check it in-game, look through binoculars before and after installing the mod. The view at
the lowest zoom should be twice as magnified, and the highest zoom twice the vanilla maximum. If you have no
binoculars, `XCreateItemInInventoryByID Binoculars_01 0 1 1` spawns a pair, which needs a console mod such as
UE4SS. CoreTweak is not yet verified in-game.

## TableDriven

`examples\TableDriven` is the pattern from [Generating patches from a script](Generating-Patches.md) as
a complete project. `table.toml` lists magazine SIDs with a new `MaxAmmo` and item SIDs with a new English name,
and `generate.py` turns it into `cfg/GameData/ItemPrototypes/TableDriven.cfg` and `text/en.toml`. Copy it like
HelloZone, with `xcopy /E /I examples\TableDriven C:\Mods\TableDriven`. Then run
`python C:\Mods\TableDriven\generate.py`, followed by `check` and `build` as usual. The generated files are
committed so that `check` works on a fresh copy, and `generate.py` writes the same output on every run. Edit
`table.toml` rather than the generated files. To check it in-game, reload each weapon with its standard magazine.
The AKM-74S magazine then holds 40 rounds instead of 30, the M10 Gordon's 32 instead of 30 and the Kora-1911's 8
instead of 7. With the game language set to English, the Medkit, Bread and Cossacks Vodka carry a `[TableDriven]`
suffix. TableDriven is not yet verified in-game.

## Options

`examples\Options` is a cfg-only mod with a main part and two options, built into a FOMOD zip as
[Optional parts and FOMOD](Optional-Parts-And-FOMOD.md) describes. The main part,
`cfg/GameData/ItemPrototypes/Options.cfg`, gives the Viper-5's standard magazine (`GunViper_MagDefault`) 40 rounds
instead of 30. The option in `Fora/`, which has `default = true`, gives the Fora-221's standard magazine
(`GunFora_MagDefault`) 40 rounds instead of 30. The option in `LightFood/` makes canned food (`CannedFood`) weigh
0.05 kg instead of 0.2 kg. `build\Options\` holds the main part and `Fora`. To try `LightFood` without a mod manager,
copy `LightFood/Options_LightFoodStalker2-Windows-OverrideContent.pak` from `build\Options-1.0.zip` into
`~mods\Options\`. To check it in-game, reload each weapon with its standard magazine, and look at the weight of
canned food in the inventory. Options is not yet verified in-game or installed through Vortex or Mod Organizer 2.
