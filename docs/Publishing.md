# Publishing

This page describes which build output to upload to Nexus Mods, and what `build.json` records.

- **Nexus Mods and Vortex.** Upload `build/<Name>-<version>.zip`. For a mod without options, it has the `<Name>/`
  folder at the archive root, which users extract into `~mods`. For a mod with options, it is a FOMOD installer, as
  [Optional parts and FOMOD](Optional-Parts-And-FOMOD.md) describes.
- **Steam Workshop.** ZonePak doesn't build for the Workshop yet. Upload Workshop mods with the Zone Kit.
- **build.json** records the ZonePak version, the mod name and version, the database name for text mods, the
  `author`, `website` and `nexus_id` from `zonepak.toml` when they are set, and the SHA-256 of each file in
  `build/<Name>/`, including the paks of options with `default = true`.
