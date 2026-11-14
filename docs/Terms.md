# Terms

This page explains the words that the other pages use.

- **Vanilla.** The game's own data without any mods. ZonePak reads it from the Zone Kit's cfg files.
- **Struct.** A named block in a cfg file, from `<name> : struct.begin` to its `struct.end`. A struct holds fields
  such as `MaxAmmo = 8` and can hold other structs.
- **Root struct.** A struct that is not inside another struct. Its name is its SID.
- **SID.** The name of a root struct in the game's tables, such as `GunPM_MagDefault` for the PM's standard
  magazine. A patch names the struct it changes by its SID.
- **refkey.** `{refkey=X}` after `struct.begin` makes the struct inherit every field of the struct with SID `X`.
- **refurl.** `{refurl=<file>}` next to a `refkey` names the cfg file that holds the `refkey` struct, when that
  struct is in another file.
- **bpatch.** `{bpatch}` after `struct.begin` marks the struct as a patch. Only the fields listed in it change, and
  every other field keeps its vanilla value.
- **Binarized table.** A GameData table the game ships in binary form as `<Table>.cfg.bin`, such as
  `ItemPrototypes`. Its patches go in a folder named after the table.
- **Plain cfg.** A GameData file the game ships as text, such as `CoreVariables.cfg`. Its patches sit beside its
  path under a `<File>.cfg_patch_<any name>` file name.
- **Culture.** A language code, such as `en` for English. Each `text/<culture>.toml` file holds the text for one
  language.
- **Database ID.** The 10-digit number in `zonepak.toml` that names the mod's generated localization database. `new`
  writes one from the current time, and every mod needs its own.
- **Option.** An optional part of a mod, with its own cfg patches and its own `.pak`. Players choose options when a
  mod manager installs the mod. The rest of the mod is the main part.
- **FOMOD.** An installer format that Vortex and Mod Organizer 2 read from a `fomod/` folder in a mod's zip. It
  shows the player a wizard to choose options.
