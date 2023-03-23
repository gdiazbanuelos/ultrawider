import winreg
import vdf
import uw_patcher
import shutil
import sys
import os
import PySimpleGUI as sg


def get_windows_registry_steam_apps():
    try:
        # Open the Steam registry key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam\\Apps")
        
        # Get the number of subkeys (installed games)
        num_games = winreg.QueryInfoKey(key)[0]
        
        # Iterate over the subkeys and get the game names
        game_names = []
        for i in range(num_games):
            game_id = winreg.EnumKey(key, i)
            game_name_key = winreg.OpenKey(key, game_id)
            try:
                if(winreg.QueryValueEx(game_name_key, "Installed")[0]):
                    #game_name = winreg.QueryValueEx(game_name_key, "Name")[0]
                    #game_names.append(game_name)
                    #print(game_id)
                    game_names.append(game_id)
                    pass
            except FileNotFoundError:
                #print(game_id)
                #print(f"Error: Could not find 'Name' value for game with ID {game_id}")
                #print("No name value", game_id)
                #game_names.append(game_id)
                pass
        
        return game_names
    except FileNotFoundError:
        print("Error: Could not find Steam registry key")
        return []


def get_steam_apps(windows_registry_steam_apps):
    libraries = vdf.parse(open('C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf'))
    libraries = libraries["libraryfolders"]

    output = []
    for lib in libraries:
        for game in libraries[lib]["apps"]:
            if(game in windows_registry_steam_apps):
                #output.append([game, libraries[lib]["path"]])
                output.append({
                    "appID": game,
                    "library": libraries[lib]["path"]
                    })
                #output["appID"] = {}
                #output["appID"]["library"] = libraries[lib]["path"]
    return output


def get_app_mainifest(steam_app):
    path_to_game_manifest = steam_app["library"]+"\steamapps\\appmanifest_{}.acf".format(steam_app["appID"])
    game_manifest = vdf.parse(open(path_to_game_manifest))
    path_to_game_files = steam_app["library"]+"\steamapps\common\\"+game_manifest["AppState"]["installdir"]
    steam_app["name"] = game_manifest["AppState"]["name"]
    steam_app["path"] = path_to_game_files


def make_target_copy(appInfo):
    try:
        os.makedirs(os.path.dirname("./backups/{}/{}".format(appInfo["appID"],appInfo["target_file"])))
        shutil.copy2(appInfo["path"], "./backups/{}/{}".format(appInfo["appID"],appInfo["target_file"]))
        print("Made a backup of {} for {} in the backups folder!".format(appInfo["target_file"], appInfo["name"]))
    except FileExistsError:
        print("Backup already exists! Game might already be patched?")


def main():
    windows_registry_steam_apps = get_windows_registry_steam_apps()
    steam_apps = get_steam_apps(windows_registry_steam_apps)
    for game in steam_apps:
        get_app_mainifest(game)
        print(game)

        # if(game["appID"] in ("319630","367520","1190460")):
        #     uw_patcher.setGameEntry(game)
        #     print(game)
        #     make_target_copy(game)
        #     offsets = uw_patcher.getOffsets(game)
        #     if(offsets != -1):
        #         uw_patcher.patchOffsets(offsets)

    return steam_apps


def createGUI(steam_apps):
    sg.theme('DarkAmber')   # Add a touch of color

    installed_games = []
    for game in steam_apps:
        installed_games.append([sg.Text(game["name"])])

    # All the stuff inside your window.
    layout = [  [sg.Text('Ultrawide Patcher')],
                installed_games,
                [sg.Text('Enter something on Row 2'), sg.InputText()],
                [sg.Button('Ok'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('Window Title', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        print('You entered ', values[0])

    window.close()


if __name__=="__main__":
    steam_apps = main()
    createGUI(steam_apps)
