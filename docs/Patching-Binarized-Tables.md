# Patching a binarized table

Use this page to change fields of structs that already exist in a binarized table such as `ItemPrototypes`,
`UpgradePrototypes` or `EffectPrototypes`. [Binarized table or plain cfg?](Binarized-Table-Or-Plain-Cfg.md) shows
how to find out which tables are binarized.

Put the patch in `cfg/GameData/<Table>/<any name>.cfg`. Subfolders inside the table folder also work. Every
`.cfg` there is a patch for that table, whatever its name.

```
GunPM_MagIncreased : struct.begin {bpatch}
   Cost = 4000.0
   Magazine : struct.begin {bpatch}
      MaxAmmo = 14
   struct.end
struct.end
```

- Put `{bpatch}` on the root struct and on every nested struct on the way down to the fields you change. `check`
  only validates inside structs that carry `{bpatch}`.
- Write array items with explicit indices that match the vanilla file, such as `[0] = GunPM_HG` or
  `[1] : struct.begin {bpatch}`. `check` does not validate index keys, so compare them with the vanilla file, as
  in [SIDs and fields](Finding-SIDs-And-Text-Keys.md#sids-and-fields).
- `removenode` deletes a field, as in `EffectPrototypeSIDs : removenode`.

Run `check`, fix what it reports, then `build` and copy `build\<Name>` into `~mods`. A cfg-only build is one
`<Name>Stalker2-Windows-OverrideContent.pak`.

A SID that gets a nested struct only through its `refkey` parent is patched the same way. For example,
`GunUDP_MagIncreased` does not define `EffectPrototypeSIDs` itself but gets it from `BigMagTemplate`. In a test on
weapon setups, a patch that set only `RecoilRadius` on a setup that inherits `RecoilParams` kept every other inherited
field. A patch on the parent setup did not reach the setups that inherit from it, and the same happened with a
technician's upgrade list in `NPCPrototypes`, so patch each SID you want to change. `check` warns when a patch sets a
field that other SIDs inherit from the patched one and the mod doesn't patch them too. Comments in the LaserTools
mod report the opposite of the first result for `LaserSight` in `ItemPrototypes`, where a partial patch on an
inheriting item is said to have dropped the inherited fields. That is unverified, so `check` also warns about a
partial patch to an inherited struct. If a patched struct misbehaves in game, list all of its fields.
