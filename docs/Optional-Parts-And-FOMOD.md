# Optional parts and FOMOD

This page covers mods with optional parts, the FOMOD installer that `build` writes for them, and how they install.

A mod can offer optional parts in one Nexus download. Vortex and Mod Organizer 2 (MO2) show them in an install
wizard, and the player ticks the ones they want. ZonePak calls these parts options and writes the wizard as a FOMOD
installer, which both mod managers read.

Declare each option in `zonepak.toml` with its own `[[option]]` table, after the other fields:

```toml
[[option]]
name = "Fora-221: 40-round magazine"
folder = "Fora"
description = "The Fora-221's standard magazine holds 40 rounds instead of 30."
image = "fomod/fora.png"
default = true

[[option]]
name = "Lighter canned food"
folder = "LightFood"
description = "Canned food weighs 0.05 kg instead of 0.2 kg."
```

Each option's patches go in its own folder in the project, laid out like the main `cfg/`:

```
MyMod/
  zonepak.toml
  cfg/GameData/ItemPrototypes/MyMod.cfg                         main part
  text/en.toml                                                  main part
  Fora/cfg/GameData/ItemPrototypes/MyMod_Fora.cfg               option Fora
  LightFood/cfg/GameData/ItemPrototypes/MyMod_LightFood.cfg     option LightFood
  fomod/fora.png                                                image for option Fora
```

- `name` is the option's label in the wizard, and `description` is the text the wizard shows for it.
- `folder` uses only letters, digits and underscores. `cfg`, `text`, `build`, `Main` and `fomod` are taken, in any
  case, and two options cannot use the same folder.
- `image` is a `.png` or `.jpg` file in the project, which the wizard shows for the option. The zip puts every image
  in `fomod/images/`, so two different images cannot have the same file name.
- `default = true` makes the option recommended. Both mod managers then tick it in advance, and `build` puts its
  pak in `build/<Name>/`. Without it, the option is unticked.

## Groups

By default the player can tick any number of options. For a set where exactly one must be picked, such as three
price levels, declare a group and put the options in it:

```toml
[[group]]
name = "Pricing"
select = "one"

[[option]]
name = "Low prices"
folder = "PriceLow"
group = "Pricing"

[[option]]
name = "Standard prices"
folder = "PriceStandard"
group = "Pricing"
default = true
```

- `name` is the group's heading in the wizard. `Options` is taken, because options without a `group` key go into a
  group of that name.
- `select = "one"` makes the player pick exactly one option of the group. `select = "any"`, the default, lets the
  player tick any number, as without a group.
- A `select = "one"` group needs exactly one option with `default = true`, so that `build/<Name>/` and
  the mod managers' defaults always hold one.
- `group` in an option names its group, compared without case. Every declared group needs at least one option.
- The wizard shows the groups in the order their first option appears in `zonepak.toml`.
- An option with `empty = true` installs nothing. Use it for the choice the main part already provides, such as
  standard prices that live in the main part, next to options that patch them to other values. It needs no
  folder, gets no pak and has no folder in the zip. An option's `{bpatch}` can change a new struct the main part
  defines, though `check` does not check those fields, and the option's file name has to sort after the main
  part's.

Options are cfg-only. Text stays in the main part, because each text database needs its own database ID and
container. A `text/` folder inside an option folder is an error. A mod with options still needs a main part with at
least one patch or text entry.

`check` checks each option's files the same way as the main `cfg/`, with the same placement rules, vanilla checks
and DLC handling. An option's findings start with its folder, as in
`Fora/cfg/GameData/ItemPrototypes/MyMod_Fora.cfg:3: error: ...`. An option with no patch files is an error unless
it has `empty = true`, and an option with `empty = true` and patch files is an error too.

Give each patch file a name that no other part of the mod uses, such as `MyMod_Fora.cfg` rather than a second
`MyMod.cfg`. Each part is its own `.pak`, and when two paks hold a file at the same path, the game reads only one of
them. `check` warns when two parts hold a file at the same path, compared without case.

When two patch files set the same field of the same SID, the game uses the file whose name sorts last, whatever
the paks are called or the mod manager's order. An option that changes a value the main part also sets needs a
file name that sorts after the main part's, such as `MyMod_Fora.cfg` after `MyMod.cfg`. `check` warns when an
option's file in a binarized table folder sorts first and sets a field the main part's file also sets. Whether
the sort ignores case is untested, so the name has to sort later both with and without case. Plain-cfg patches are
not checked, since the order there is untested.

## What build writes for a mod with options

`build` packs the main part the same way as for a mod without options. Each option gets its own cfg-only pak,
`<Name>_<folder>Stalker2-Windows-OverrideContent.pak`, packed and mounted the same way as a cfg-only main pak. For
the [Options example](Examples.md#options):

```
build/
  Options/                          main part and the options with default = true, for ~mods
    OptionsStalker2-Windows-OverrideContent.pak
    Options_ForaStalker2-Windows-OverrideContent.pak
  Options-1.0.zip                   FOMOD installer for Nexus
  build.json
```

The zip holds:

```
fomod/info.xml
fomod/ModuleConfig.xml
fomod/images/<file>                 the option images, if any
Main/OptionsStalker2-Windows-OverrideContent.pak
Fora/Options_ForaStalker2-Windows-OverrideContent.pak
LightFood/Options_LightFoodStalker2-Windows-OverrideContent.pak
```

`ModuleConfig.xml` always installs `Main/` and offers the options on one wizard page, one group at a time, in the
order `zonepak.toml` lists them. The player can pick any number of a group's options, or none, except in a
`select = "one"` group, where they pick exactly one. Every folder installs to the mod's own folder, so the
chosen paks end up side by side. `info.xml` holds `friendly_name`, `author`, `version`, `nexus_id` (as `Id`),
`website` and `description`, and leaves out the empty ones. A mod without options builds exactly as before, with no
`fomod/` folder in the zip.

## Installing a mod with options

`build/<Name>/` holds the main part and the options with `default = true`, so copying it into `~mods` installs
those. To try an option without `default = true`, copy its `.pak` from the zip into `~mods\<Name>\`, or
set `default = true` and build again.

What the mod managers do with the zip comes from reading their source code on 2026-11-04, not from tests:

- Vortex installs every zip with a `fomod/ModuleConfig.xml` through its own FOMOD installer, and refuses a
  `ModuleConfig.xml` that does not match the FOMOD schema. ZonePak's tests check the generated file against a copy
  of that schema when `lxml` is installed.
- With version 2.1.1 or newer of Vortex's STALKER 2 extension, Vortex treats the installed mod as a sortable pak mod
  and deploys the chosen paks to `~mods\<prefix>-<Vortex mod ID>\`, where the prefix sets the load order. Older
  versions put the paks straight into `~mods\`.
- MO2 has no STALKER 2 support of its own. The community plugin mo2s2 says it supports FOMOD installers, and its code
  moves paks at the root of an installed mod into `Stalker2\Content\Paks\~mods`.
- MO2 reads `Name`, `Author`, `Version`, `Id` and `Website` from `info.xml`. With `nexus_id` set, it can check Nexus
  for updates of a manually downloaded mod. Vortex does not read `info.xml`.
- Both managers tick the options with `default = true` in advance.

Not yet verified:

- That paks Vortex deploys from a FOMOD to `~mods\<prefix>-<Vortex mod ID>\` load in-game. Other FOMOD pak mods,
  such as Dynamic Weather Overhaul, suggest they do.
- How mo2s2 handles a FOMOD install.
- How Vortex and MO2 find option images. ZonePak writes the image path from the zip root, as `fomod/images/<file>`,
  which is how Dynamic Weather Overhaul's FOMOD does it.
