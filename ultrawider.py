import vdf
import patcher
import shutil
import sys
import os
import PySimpleGUI as sg
import re
from sys import platform
from pathlib import Path
import json

# Global list of all installed Steam apps
# Example entry:
# {'appID': '374320', 'library': 'D:\\SteamLibraryD', 'name': 'DARK SOULS III', 'path': WindowsPath('D:/SteamLibraryD/steamapps/common/DARK SOULS III')}
steam_apps = None
steam_path = None
backupout = None
restoreout = None


def get_steam_apps():
    global steam_path
    steam_path = ""
    if platform == "linux" or platform == "linux2":
        steam_path = Path(
            "/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
        if (steam_path.exists()):
            print("Found default Steam '{}' file!".format(steam_path.name))
            pass
        else:
            print("Failed to find default Steam '{}' file!".format(steam_path.name))
            pass
    elif platform == "darwin":
        # OS X
        pass
    elif platform == "win32":
        steam_path = Path(
            'C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf')
        if (steam_path.exists()):
            print("Found default Steam '{}' file!".format(steam_path.name))
            pass
        else:
            print("Failed to find default Steam '{}' file!".format(steam_path.name))
            pass

    libraries = vdf.parse(open(steam_path))
    libraries = libraries["libraryfolders"]

    output = []
    # Get all games installed that are listed in the default Steam libraryfolders.vdf
    for lib in libraries:
        for game in libraries[lib]["apps"]:
            output.append({
                "appID": game,
                "library": libraries[lib]["path"]
            })

    # Manually search all appmanifest_xxx.acf files at each Steam library location
    # for some reason, not all installed games are written to libraryfolders.vdf
    for lib in libraries:
        steam_library_paths = libraries[lib]["path"]
        manifest_path = Path(steam_library_paths + "/steamapps")
        directory_list = os.listdir(manifest_path)
        for files in directory_list:
            if (re.match("^appmanifest_.*\.acf$", files)):
                gameID = re.sub("appmanifest_|\.acf", "", files)
                gameEntry = {"appID": gameID, "library": steam_library_paths}
                if gameEntry not in output:
                    output.append(gameEntry)
    return output


def get_app_mainifest(steam_app):
    path_to_game_manifest = Path(steam_app["library"] +
                                 "/steamapps/appmanifest_{}.acf".format(steam_app["appID"]))
    game_manifest = vdf.parse(open(path_to_game_manifest))
    path_to_game_files = Path(steam_app["library"] +
                              "/steamapps/common/"+game_manifest["AppState"]["installdir"])
    steam_app["name"] = game_manifest["AppState"]["name"]
    steam_app["name"] = re.sub(
        r'[^A-Za-z0-9`~!@#$%^&*()-_=+;:\'\"\,.<>/?\{\} ]+', '', steam_app["name"])
    steam_app["path"] = path_to_game_files


def make_target_copy(appInfo):
    global backupout
    backuppath = Path(
        "./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"]))
    try:
        os.makedirs(os.path.dirname(
            Path(backuppath)))
        shutil.copy2(
            appInfo["absolute_path"], backuppath)
        backupout = ("Made a backup of unpatched file '{}' for {} in the backups folder:\n{}".format(
            appInfo["target_file"], appInfo["name"], backuppath))
        # print(backupout)

        # Creates a new file
        with open(Path("./backups/{}/{}.txt".format(appInfo["appID"], appInfo["name"])), 'w') as fp:
            fp.write("This folder is a backup for the patched {} file".format(
                appInfo["name"]))

    except FileExistsError:
        backupout = "Backup already exists! Game might already be patched?"
        # print(backupout)


def get_installed_games():
    steam_apps = get_steam_apps()
    for game in steam_apps:
        get_app_mainifest(game)
    return steam_apps


def patchGame(steam_app):
    patcher.setGameEntry(steam_app)
    if (patcher.getOffsets(steam_app)):
        make_target_copy(steam_app)
        return patcher.patchOffsets(steam_app)
    else:
        print("Hex patterns not found! Game might already be patched?")


def get_selected_game(appID):
    for game in steam_apps:
        if (appID == game["appID"]):
            # print(game)
            return game


def openJSON(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def restore_backup(steam_app):
    global restoreout
    backup_path = Path(
        "./backups/{}/{}".format(steam_app["appID"], steam_app["target_file"]))
    try:
        shutil.copy2(
            backup_path, steam_app["absolute_path"])
        restoreout = ("Restored unpatched '{}' file for {} to:\n{}".format(
            steam_app["target_file"], steam_app["name"], steam_app["absolute_path"]))
        print(restoreout)

    except FileNotFoundError:
        restoreout = "No backup files exists for {} under \"{}\"!".format(
            steam_app["name"], backup_path)
        print(restoreout)

def createGUI():
    global steam_apps
    sg.theme('DarkAmber')   # Add a touch of color

    bundle_dir = getattr(
        sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_help = os.path.abspath(os.path.join(bundle_dir, 'games.json'))
    patch_list_dictionary = openJSON(path_to_help)

    patch_list = list(patch_list_dictionary.keys())
    installed_games = []
    for game in steam_apps:
        if game["appID"] in patch_list:
            installed_games.append(
                "{}  ({})".format(game["name"], game["appID"]))

    # All the stuff inside your window.
    layout = [[sg.Text(text='Ultrawider',
                       font=('Arial Bold', 20),
                       size=20,
                       expand_x=True,
                       justification='center')],
              [sg.Text("Default Steam install library path: " + str(steam_path))],
              [sg.Text('Number of patchable Steam Apps installed: ' +
                       str(len(installed_games)))],
              [sg.Listbox(values=installed_games, size=(100, 15),
                          enable_events=True, key='-LIST-')],
              [sg.Text('Select a game to patch!', key='-CURRENTGAME-'), sg.Button("Patch!", key='CURRENTGAME'), sg.Button("Patch FOV!", key='pf', visible=False)],
              [sg.Text(text="Backup file found!", key="BACKUPTEXT", visible=False),sg.Button("Restore!", key='CURRENTGAMERESTORE', visible=False)],
              [sg.Text("", key="-BACKUPOUTPUT-")],
              [sg.Text("", key="-OUTPUT-")]]

    # Create the Window
    window = sg.Window('Ultrawider', layout, icon=("./marthi.ico"))
    # Event Loop to process "events" and get the "values" of the inputs
    selected_game = []
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == "-LIST-":
            window['-CURRENTGAME-'].update(values['-LIST-'][0])

            pattern = r"\(([^()]+)\)[^()]*$"
            appID = re.findall(pattern, values['-LIST-'][0])[-1]
            app = get_selected_game(appID)
            patcher.setGameEntry(app)
            #print(app)
            if (app["3440_1440_hex_fov_pattern"] != None):
                window['pf'].update(visible=True)
            else:
                window['pf'].update(visible=False)
            
            path = Path("./backups/{}/{}".format(app["appID"], app["target_file"]))
            print(path)
            if(path.is_file()):
                window['BACKUPTEXT'].update(visible=True)
                window['CURRENTGAMERESTORE'].update(visible=True)
            else:
                window['BACKUPTEXT'].update(visible=False)
                window['CURRENTGAMERESTORE'].update(visible=False)
            selected_game = values['-LIST-']
            window['-BACKUPOUTPUT-'].update("")
            window['-OUTPUT-'].update("")
            
        if event == "CURRENTGAME":
            pattern = r"\(([^()]+)\)[^()]*$"
            appID = re.findall(pattern, selected_game[0])[-1]
            app = get_selected_game(appID)
            if (patchGame(app)):
                window['-BACKUPOUTPUT-'].update(backupout)
                output = "Patching successful! Patched {} file for {} under:\n{}".format(
                    app["target_file"], app["name"], app["absolute_path"])
                window['-OUTPUT-'].update(output)
            else:
                window['-BACKUPOUTPUT-'].update(backupout)
                window['-OUTPUT-'].update(
                    "Hex offset pattern not found! Game might already be patched?")
        if event == 'CURRENTGAMERESTORE':
            pattern = r"\(([^()]+)\)[^()]*$"
            appID = re.findall(pattern, selected_game[0])[-1]
            app = get_selected_game(appID)
            patcher.setGameEntry(app)
            restore_backup(app)
            window['-BACKUPOUTPUT-'].update(restoreout)
            window['-OUTPUT-'].update("")

    window.close()


def main():
    global steam_apps
    steam_apps = get_installed_games()
    createGUI()


if __name__ == "__main__":
    main()
