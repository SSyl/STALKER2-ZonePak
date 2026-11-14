# Adding new structs

This page covers adding structs that vanilla does not have.

New structs, such as new effects or upgrades, are root structs without `{bpatch}` whose SID does not exist in
vanilla. Put them in the same place as patches for that table.

```
MyMod_CarryweightEffect : struct.begin {refkey=DutyArmor_4_E1_CarryweightEffect}
   SID = MyMod_CarryweightEffect
   ValueMin = 30.0%
   ValueMax = 30.0%
struct.end
```

- `refkey` can name a vanilla struct in the same table or a new struct defined in any of the mod's files for the
  same table. In a mod with [options](Optional-Parts-And-FOMOD.md), an option's struct can also name a new struct of
  the main part, which is always installed. It cannot name another option's new struct, and the main part cannot
  name an option's, because the player may not install that option. `check` reports an error when `refkey` names
  none of these. `refkey` values that start with `[`, and structs with `refurl`, are not checked.
- A new struct only has an effect once something uses its SID, for example a patched item or upgrade that lists
  it among its effects.
- A root without `{bpatch}` whose SID already exists replaces the whole vanilla struct, as GSC's KB 145 (Config
  patches) describes, and `check` warns about it.
