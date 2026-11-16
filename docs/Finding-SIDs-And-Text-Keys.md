# Finding SIDs, fields and text keys

This page shows where to look up the SIDs, fields and text keys that a patch or a text override names.

## SIDs and fields

The Zone Kit, lesser or full, holds the vanilla GameData as plain-text cfg files under
`<zone_kit>\Stalker2\Content\GameLite\GameData\`. Open them in any text editor, or search them with `findstr` in a
command prompt. This command finds where the PM's standard magazine is defined. Use your own `zone_kit` folder
in the path. GameData holds about 150,000 files, so the search can take several minutes.

```
findstr /S /N /C:"GunPM_MagDefault :" "D:\Games\Epic Games\STALKER2ZoneKit\Stalker2\Content\GameLite\GameData\*.cfg"
```

```
D:\Games\Epic Games\STALKER2ZoneKit\Stalker2\Content\GameLite\GameData\ItemPrototypes\AttachPrototypes.cfg:1361:GunPM_MagDefault : struct.begin {refkey=MagTemplate}
```

The result gives the file, the line number and the line. Open the file at that line to see the fields the struct
defines. Fields it does not list come from its `refkey` parent, here `MagTemplate`, which you can find the same
way. The file's path also tells you where the patch goes, as
[Binarized table or plain cfg?](Binarized-Table-Or-Plain-Cfg.md) explains.

## Text keys

A text override replaces the text of one localization key. `text` searches the game's own text, read from
`pakchunk0-Windows.pak`, for a key or a text that contains your search, in any case:

```
python -m zonepak text bandage
```

```
sid_items_Bandage_description = "A dressing to stop bleeding, possibly even sterile. Handy for bandaging wounds, stopping arterial bleeding, and preventing infection."
sid_items_Bandage_name = "Bandage"
...
37 match(es)
```

Each line is in the form a text file takes, so you can copy it into `text/en.toml` and change the text.
`--culture de` searches and prints the German text instead, and `--limit 0` prints every match instead of the first
50. Add `> found.txt` to save the output to a file, which ZonePak writes as UTF-8.

Item and upgrade names also follow fixed patterns:

- An item's name uses the key `sid_items_<SID>_name`, for example `sid_items_Bandage_name`. When the item defines
  `LocalizationSID`, the key uses that value in place of the SID. The weapon `GunKora_HG` has
  `LocalizationSID = myriflepack_GunKora_HG`, so its name key is `sid_items_myriflepack_GunKora_HG_name`. This
  rule was read from the game's own data. GSC does not document it.
- An upgrade's name and description use `sid_upgrades_<SID>_name` and `sid_upgrades_<SID>_description`.
- Faction names use `sid_misc_faction_<faction>`, for example `sid_misc_faction_duty` ("Duty"),
  `sid_misc_faction_neutrals` ("Lone Stalkers") and `sid_misc_faction_varta` ("The Ward"). Bandits and Monolith
  have no key in that family. They are `sid_misc_answer_faction_Bandits` and `sid_misc_answer_faction_Monolith`.

The game looks a key up in each namespace listed under `[/Script/Stalker2.GameLocalizationSettings]` in the Zone
Kit's `Stalker2\Config\DefaultGame.ini`, starting with `ST_S2BaseGameLocalization`. Text overrides work through
that lookup. A Blueprint text literal with that namespace and a key does not. The game's `Game.locres` stores 0 as
every source-string hash, so the engine treats the literal's text as out of date and shows its source string in
every language.
