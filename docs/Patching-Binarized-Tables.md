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

If a SID gets a nested struct only through its `refkey` parent, `check` warns that the struct is inherited. For
example, `GunUDP_MagIncreased` does not define `EffectPrototypeSIDs` itself but gets it from `BigMagTemplate`. A
partial patch of such a struct can drop the inherited fields, so either list all of them or patch the parent. The
source for this rule is the comments in the LaserTools mod's `zzz_LaserToolsX_LaserVFX.cfg`.
