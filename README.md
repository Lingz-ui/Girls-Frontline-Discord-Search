# Girls' Frontline Discord Search
Search a doll from Girls' Frontline within Discord.

Features:
- Type, Base Stats, Max Stats, How To Obtain, Production Requirement, Ability, Ability Cooldown, Tile Bonus, Tile Bonus information.
- placebo recipies and estimated drop rates for rare dolls.
- Embed color matches star color
- Links to the corresponding doll page on https://en.gfwiki.com
- Flavor text.
- Aliases.

Coming eventually:
- MOD1, MOD2, MOD3
- $gfimage costume support
- $gffilter for finding the best doll in a type.

## Commands
Assuming that that the default prefix $gf is still being used:
- $gfsearch: Search a doll
- $gfimage: Display only the image for that doll.
- $gfhelp: List commands, version, etc
- $gfquote: Show quotes from the dolls if you have CharacterVoice.json from the game files
- $gfstatus: Number of servers this bot is in.

## Prerequesites
Python3 and pip

## Setup
1. `git clone https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search.git`
2. edit main.py, insert your discord bot token in DISCORD_TOKEN
3. Change COMMAND_PREFIX to whatever you want, the default is $gf
4. If you have your own server containing the dumped girls frontline images, change PIC_DOMAIN, otherwise you can keep using mine.
5. `pip3 install discord` (Windows users, the command might be 'pip' instead of pip3)
6. `chmod +x run_forever.sh` (Windows users, you're on your own)
7. `./run_forever.sh` if linux, otherwise `python3 main.py`.

### How to enable $gfquote and get your own images
https://github.com/36base/girlsfrontline-resources-extract

## Legal stuff
main.py is GPL, read LICENCE for more information.

THIS PROGRAM IS NOT ENDORSED BY https://en.gfwiki.com. ALL DATA CONTAINED WITHIN girlsfrontline.json IS Ⓒ https://en.gfwiki.com AND LICENCED UNDER CC BY-SA 3.0. For more information, please read gf_json_LICENCE.

## Screenshot
![GFSearch Command](https://i.imgur.com/QAkHNF5.png)
