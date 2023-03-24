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


def get_steam_apps():
    global steam_path
    steam_path = ""
    if platform == "linux" or platform == "linux2":
        steam_path = Path(
            "/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
        if (steam_path.exists()):
            print("Found default Steam '{}' file!".format(steam_path.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_path.name))
    elif platform == "darwin":
        # OS X
        pass
    elif platform == "win32":
        steam_path = Path(
            'C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf')
        if (steam_path.exists()):
            print("Found default Steam '{}' file!".format(steam_path.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_path.name))

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
    try:
        os.makedirs(os.path.dirname(
            Path("./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"]))))
        shutil.copy2(
            appInfo["path"], Path("./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"])))
        backupout = ("Made a backup of '{}' for {} in the backups folder!".format(
            appInfo["target_file"], appInfo["name"]))
        print(backupout)
        
        # Creates a new file
        with open(Path("./backups/{}/{}.txt".format(appInfo["appID"], appInfo["name"])), 'w') as fp:
            fp.write("This folder is a backup for the patched {} file".format(appInfo["name"]))



    except FileExistsError:
        backupout = "Backup already exists! Game might already be patched?"
        print(backupout)


def get_installed_games():
    steam_apps = get_steam_apps()
    for game in steam_apps:
        get_app_mainifest(game)
    return steam_apps


def patchGame(steam_app):
    patcher.setGameEntry(steam_app)
    make_target_copy(steam_app)
    offsets = patcher.getOffsets(steam_app)
    if (offsets != -1):
        return patcher.patchOffsets(offsets)


def get_selected_game(appID):
    for game in steam_apps:
        if (appID == game["appID"]):
            print(game)
            return game


def openJSON(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def createGUI():
    global steam_apps
    sg.theme('DarkAmber')   # Add a touch of color

    patch_list_dictionary = openJSON("games.json")
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
              [sg.Text('Select a game to patch!', key='-CURRENTGAME-'),
               sg.Button("Patch!", key='CURRENTGAME')],
              [sg.Text("", key="-BACKUPOUTPUT-")],
              [sg.Text("", key="-OUTPUT-")]]

    # Create the Window
    window = sg.Window('Ultrawider', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    selected_game = []
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == "-LIST-":
            window['-CURRENTGAME-'].update(values['-LIST-'][0])
            selected_game = values['-LIST-']
            window['-BACKUPOUTPUT-'].update("")
            window['-OUTPUT-'].update("")
        if event == "CURRENTGAME":
            pattern = r"\(([^()]+)\)[^()]*$"
            appID = re.findall(pattern, selected_game[0])[-1]
            app = get_selected_game(appID)
            if (patchGame(app)):
                window['-BACKUPOUTPUT-'].update(backupout)
                window['-OUTPUT-'].update("Patching successful")
            else:
                window['-BACKUPOUTPUT-'].update(backupout)
                window['-OUTPUT-'].update(
                    "Hex offset pattern not found! Game might already be patched?")
    window.close()


def main():
    global steam_apps
    steam_apps = get_installed_games()
    createGUI()


if __name__ == "__main__":
    main()
