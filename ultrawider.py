import vdf
import patcher
import shutil
import sys
import os
import PySimpleGUI as sg
import re
from sys import platform
from pathlib import Path


def get_steam_apps():
    steam_path = ""
    if platform == "linux" or platform == "linux2":
        steam_path = Path("/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
        if(steam_path.exists()):
            print("Found default Steam '{}' file!".format(steam_path.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_path.name))
    elif platform == "darwin":
        # OS X
        pass
    elif platform == "win32":
        steam_path = Path('C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf')
        if(steam_path.exists()):
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
    path_to_game_manifest = Path(steam_app["library"] + \
        "/steamapps/appmanifest_{}.acf".format(steam_app["appID"]))
    game_manifest = vdf.parse(open(path_to_game_manifest))
    path_to_game_files = Path(steam_app["library"] + \
        "/steamapps/common/"+game_manifest["AppState"]["installdir"])
    steam_app["name"] = game_manifest["AppState"]["name"]
    steam_app["name"] = re.sub(
        r'[^A-Za-z0-9`~!@#$%^&*()-_=+;:\'\"\,.<>/?\{\} ]+', '', steam_app["name"])
    steam_app["path"] = path_to_game_files


def make_target_copy(appInfo):
    try:
        os.makedirs(os.path.dirname(
            Path("./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"]))))
        shutil.copy2(
            appInfo["path"], Path("./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"])))
        print("Made a backup of {} for {} in the backups folder!".format(
            appInfo["target_file"], appInfo["name"]))
    except FileExistsError:
        print("Backup already exists! Game might already be patched?")


def get_installed_games():
    steam_apps = get_steam_apps()
    for game in steam_apps:
        get_app_mainifest(game)
        print(game)
        if(game["appID"] in ("319630","367520","1190460")):
            #patchGame(game)
            pass
            

    print("Number of Steam Apps installed:", len(steam_apps))
    return steam_apps


def patchGame(steam_app):
    patcher.setGameEntry(steam_app)
    #print(steam_app)
    make_target_copy(steam_app)
    offsets = patcher.getOffsets(steam_app)
    if(offsets != -1):
        patcher.patchOffsets(offsets)


def createGUI(steam_apps):
    sg.theme('DarkAmber')   # Add a touch of color

    installed_games = []
    for game in steam_apps:
        installed_games.append(
            "{}  (ID:{})".format(game["name"], game["appID"]))

    # All the stuff inside your window.
    layout = [[sg.Text(text='Ultrawider',
                       font=('Arial Bold', 20),
                       size=20,
                       expand_x=True,
                       justification='center')],
              [sg.Text('Number of Steam Apps installed: ' +
                       str(len(installed_games)))],
              [sg.Listbox(values=installed_games, size=(100, 15),
                          enable_events=True, key='-LIST-')],
              [sg.Text('Select a game to patch!', key='-CURRENTGAME-')]]

    # Create the Window
    window = sg.Window('Ultrawider', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == "-LIST-":
            window['-CURRENTGAME-'].update(values['-LIST-'][0])
    window.close()


def main():
    steam_apps = get_installed_games()
    createGUI(steam_apps)


if __name__ == "__main__":
    main()
