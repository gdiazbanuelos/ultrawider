import winreg
import vdf
import patcher
import shutil
import sys
import os
import PySimpleGUI as sg
import re


def get_windows_registry_steam_apps():
    try:
        # Open the Steam registry key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             "Software\\Valve\\Steam\\Apps")

        # Get the number of subkeys (installed games)
        num_games = winreg.QueryInfoKey(key)[0]

        # Iterate over the subkeys and get the game names
        game_names = []
        for i in range(num_games):
            game_id = winreg.EnumKey(key, i)
            game_name_key = winreg.OpenKey(key, game_id)
            try:
                if (winreg.QueryValueEx(game_name_key, "Installed")[0]):
                    # game_name = winreg.QueryValueEx(game_name_key, "Name")[0]
                    # game_names.append(game_name)
                    # print(game_id)
                    game_names.append(game_id)
                    pass
            except FileNotFoundError:
                print(
                    f"Error: Could not find 'Name' value for game with ID {game_id}")
                pass

        return game_names
    except FileNotFoundError:
        print("Error: Could not find Steam registry key")
        return []


def get_steam_apps(windows_registry_steam_apps):
    libraries = vdf.parse(
        open('C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf'))
    libraries = libraries["libraryfolders"]

    output = []
    # Get all games installed that are listed in the default Steam libraryfolders.vdf
    for lib in libraries:
        for game in libraries[lib]["apps"]:
            if (game in windows_registry_steam_apps):
                output.append({
                    "appID": game,
                    "library": libraries[lib]["path"]
                })

    # Manually search all appmanifest_xxx.acf files at each Steam library location
    # for some reason, not all installed games are written to libraryfolders.vdf
    for lib in libraries:
        steam_library_paths = libraries[lib]["path"]
        manifest_path = steam_library_paths + "\steamapps"
        directory_list = os.listdir(manifest_path)
        for files in directory_list:
            if (re.match("^appmanifest_.*\.acf$", files)):
                gameID = re.sub("appmanifest_|\.acf", "", files)
                gameEntry = {"appID": gameID, "library": steam_library_paths}
                if gameEntry not in output:
                    output.append(gameEntry)
    return output


def get_app_mainifest(steam_app):
    path_to_game_manifest = steam_app["library"] + \
        "\steamapps\\appmanifest_{}.acf".format(steam_app["appID"])
    game_manifest = vdf.parse(open(path_to_game_manifest))
    path_to_game_files = steam_app["library"] + \
        "\steamapps\common\\"+game_manifest["AppState"]["installdir"]
    steam_app["name"] = game_manifest["AppState"]["name"]
    steam_app["name"] = re.sub(r'[^A-Za-z0-9`~!@#$%^&*()-_=+;:\'\"\,.<>/?\{\} ]+', '', steam_app["name"])
    steam_app["path"] = path_to_game_files


def make_target_copy(appInfo):
    try:
        os.makedirs(os.path.dirname(
            "./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"])))
        shutil.copy2(
            appInfo["path"], "./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"]))
        print("Made a backup of {} for {} in the backups folder!".format(
            appInfo["target_file"], appInfo["name"]))
    except FileExistsError:
        print("Backup already exists! Game might already be patched?")


def get_installed_games():
    windows_registry_steam_apps = get_windows_registry_steam_apps()
    steam_apps = get_steam_apps(windows_registry_steam_apps)
    for game in steam_apps:
        get_app_mainifest(game)
        print(game)

        # if(game["appID"] in ("319630","367520","1190460")):
        #     patcher.setGameEntry(game)
        #     print(game)
        #     make_target_copy(game)
        #     offsets = patcher.getOffsets(game)
        #     if(offsets != -1):
        #         patcher.patchOffsets(offsets)

    print("Number of Steam Apps installed:", len(steam_apps))
    return steam_apps


def createGUI(steam_apps):
    sg.theme('DarkAmber')   # Add a touch of color

    installed_games = []
    for game in steam_apps:
        installed_games.append("{}  (ID:{})".format(game["name"], game["appID"]))

    # All the stuff inside your window.
    layout = [[sg.Text(text='Ultrawider',
                       font=('Arial Bold', 20),
                       size=20,
                       expand_x=True,
                       justification='center')],
              [sg.Text('Number of Steam Apps installed: ' +
                       str(len(installed_games)))],
              [sg.Listbox(values=installed_games,size=(100, 15), enable_events=True, key='-LIST-')],
              [sg.Text('Select a game to patch!', key='-CURRENTGAME-')]]

    # Create the Window
    window = sg.Window('Ultrawider', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == "-LIST-":
            window['-CURRENTGAME-'].update(values['-LIST-'])
        print(event)
    window.close()


def main():
    steam_apps = get_installed_games()
    createGUI(steam_apps)


if __name__ == "__main__":
    main()
