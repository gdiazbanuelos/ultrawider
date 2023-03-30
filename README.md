# Ultrawider
 An auto patcher for select games to be enjoyed in glorious 21:9 ultrawide
<br/><hr/>
MFW a game doesn't have native ultrawide support


![alt text](marthi.png)

# GUI
![My Image](ultrawider3.png)

How it works:

- To patch in another aspect ratio, we must change the hex patterns at certain offsets for a game's files
- We do this with hexalter.c which takes offset locations (ie. 0x3f) for an input file (ie. game.exe) and overrides the offset with the patch (ie 0x18), patching in the aspect ratio
- Before patching the files, we make a backup under ./backups/{apppID}/{patched_file}
- Then the program patches the files at the game's install location
- The restore button shows up once the backup is made, allowing for easy undoing of the patch

# Supported Games
Game Name (Steam App ID)
<br/>*App ID's can be found in the url of a game's Steam store page*
<br/> *Hollow Knight: https://store.steampowered.com/app/367520/Hollow_Knight/*
- Hollow Knight (367520)
- Horizon Zero Dawn (1151640)
- Life is Strange (319630)
- Life is Strange: True Colors (936790)
- Death Stranding (1190460)

# Install
- Download latest release: https://github.com/gdiazbanuelos/ultrawider/releases
- Windows file: `ultrawider.exe`
- Linux file: `ultrawider` (Wine must be installed! Future plans to remove this dependency)

# Future updates
- Patch FOV values
- Added ability to patch other aspect ratios (32:9, 16:10, other 21:9 non 3400x1440 resolutions)
- Highlight already patched games in green
- If default Steam location is not found, ability to manually select Steam install folder
- Add JSON file to final build so that anyone can manually add games to patcher tool
- Remove need of Wine for Linux build

# Building Ultrawider
- Install Python
- Install Pip3 packages: `pip3 install vdf pysimplegui pyinstaller`
- Or run `pip3 install -r requirements.txt`
<br/><br/>
- To build on Windows: `python -m PyInstaller .\ultrawider.py --clean -F --add-data="games.json;." --add-data="hexalter.exe;." `
- To build on Linux: `pyinstaller ultrawider.py --clean -F --add-data "games.json:." --add-data "hexalter.exe:."`
- Or on Windows: `.\build.ps1`
- Or on Linux: `./build.sh`
- Alternatively only build `ultrawider.exe` on your platform without the `-add-data` commands, then place `games.json` and/or `hexalter.exe` in the `./dest` folder
<br/><br/>
If you want to build `hexalter.exe` yourself, run `gcc -o hexalter.exe hexalter.c`
