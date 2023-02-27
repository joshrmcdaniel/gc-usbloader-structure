# usb-loader-gx gamecube file structurer
When I attempted to import my games via GCBM, it did not work. However, I was able to create a file from gcbm with all the games with the relevant information.<br>
This script will automatically structure the games on your drive to the format USB Loader GX is looking for

## Requirements
`pip install loguru pandas requests xmltodict` or `pip install -r requirements.txt`

## Usage
Env file should have the following:
```
ISO_PATH=<path to gc isos>
DEST_PATH=<path to structure the isos (i.e.: /mnt/ext/games/)>
GAME_CSV=<path to gcbm export>
IMAGE_PATH=<path to save game images to>
TDB_LANG=<lang to grab from tdb (not implemented)>
WIIWARE=<grab wiiware from tdb (not implemented)>
GAMECUBE<game gamecube info from tdb (not implemented)>
```
## Convert exported gcbm list to tsv requested
Do this in the order specified (works in vscode, modify if using different ide/regex parser)
1. `(\|\s+)(path/to/isos.+?,.+?)(\s+\|)` to be replaced with `$1"$2"$3`
2. Remove matches of `^-+$\n`
3. Remove matches of `\s+\|(\s+)?`