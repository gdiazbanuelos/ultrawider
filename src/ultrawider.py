import subprocess
import PySimpleGUI as sg
import vdf
import os
import sys
from sys import platform
from pathlib import Path
import re
import json
import ast
import shutil
import textwrap

steam_lib_filepath = None
steam_libraries = None


steam_paths = None
steam_apps = None
filtered_apps = None
current_game = None
path_to_patcher_exe = None


# PySimpleGui class text strings
window = None
backup_output = ""

aspect_ratio_list = ['21:9 (3440x1440)', '21:9 (2560x1080)','21:9 (3840x1600)']
selected_aspect_ratio = aspect_ratio_list[0]

# Find all installed Steam Games
# Find libfolders.vdf, search default location for OS
# If not in default location, prompt to manually input location libfolders.vdf
def get_steam_lib_filepath():
    global steam_lib_filepath
    global steam_libraries
    global path_to_patcher_exe

    # Try default Steam install location
    if platform == "linux" or platform == "linux2":
        steam_lib_filepath = Path(
            "/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        path_to_patcher_exe = os.path.abspath(os.path.join(bundle_dir,'hexalter'))
        if (steam_lib_filepath.exists()):
            print("Found default Steam '{}' file!".format(steam_lib_filepath.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_lib_filepath.name))
            steam_lib_filepath = None
            return
    elif platform == "darwin":
        # OS X
        pass
    elif platform == "win32":
        steam_lib_filepath = Path(
            'C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf')
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        path_to_patcher_exe = os.path.abspath(os.path.join(bundle_dir,'hexalter.exe'))
        if (steam_lib_filepath.exists()):
            print("Found default Steam '{}' file!".format(steam_lib_filepath.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_lib_filepath.name))
            steam_lib_filepath = None
            return


def createGUI():
    global window
    global steam_lib_filepath

    sg.theme('DarkAmber')

    layout = [
        [sg.T('Ultrawider',
              font=('Arial Bold', 25),
              size=20,
              expand_x=True,
              justification='center')],
        [sg.Text("Steam Library File", font=(15)),
         sg.In(key="-STEAM_LIB_FILEPATH-", default_text=steam_lib_filepath,size=(55, 1), font=(15),
               change_submits=True, enable_events=True), sg.FileBrowse()],
        [sg.T("")],
        [sg.T("Aspect Ratio", font=(30)), sg.Combo(aspect_ratio_list, key='-ASPECT_RATIO-', 
                                                   default_value=aspect_ratio_list[0], 
                                                   size=(30), readonly=True, enable_events=True,
                                                   font=(15))],
        [sg.T("")],
        [sg.Listbox(values=[], size=(200, 10), font=(15), enable_events=True, key='-LIST-', visible=False)],
        [sg.T("", key='-CURRENT_GAME-')],
        [sg.T("", key='-DESCRIPTION-', font=(15))],
        [sg.T()],
        [sg.Button('Patch', visible=False), sg.Button('Restore', visible=False)],
        [sg.T()],
        [sg.Multiline(size=(200,10), key='-OUTPUT_BOX-', autoscroll=True, visible=False)]
    ]

    screen_x, screen_y = sg.Window.get_screen_size()
    window_x, window_y = 800, 700
    window = sg.Window('', layout, finalize=True, size=(window_x,window_y), location=(screen_x/2 - window_x/2,screen_y/2 - window_y/2))


def guiLoop():
    global window
    global steam_lib_filepath
    global selected_aspect_ratio

    if(steam_lib_filepath != None):
        get_steam_apps()
        get_app_mainifests()
        filter_apps()
        window['-LIST-'].update(values=filtered_apps, visible=True)
    else:
        window['-OUTPUT_BOX-'].update("Error! Find the \"libraryfolders.vdf\" file under <path_to_steam>/Steam/steamapps/\n", 
        background_color="red", text_color="white", append=True, visible=True)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()            
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if event == '-LIST-':
            select_Game_GUI(values)
        if event == 'Patch':
            patch_game()
        if event == 'Restore':
            restore_backup(current_game)
        if event == '-ASPECT_RATIO-':
            change_selected_aspect_ratio(values)
            resetGUI(values)
        if event == '-STEAM_LIB_FILEPATH-':
            resetGUI(values)
    window.close()


def change_selected_aspect_ratio(values):
    global selected_aspect_ratio
    selected_aspect_ratio = values['-ASPECT_RATIO-']


def restore_backup(steam_app):
    global backup_output

    backup_path = Path(
        "./backups/{}/{}".format(steam_app["appID"], steam_app["target_file"]))
    try:
        shutil.copy2(backup_path, steam_app["target_file_path"])
        backup_output = 'Back up of original file \'{}\' for {} was restored to:\n{}'\
            .format(steam_app["target_file"], steam_app["name"], steam_app["target_file_path"])
        window['-OUTPUT_BOX-'].update(backup_output+'\n\n', append=True, visible=True)
    except FileNotFoundError:
        backup_output = 'Restore of original back failed! Backup file was not found!'
        window['-OUTPUT_BOX-'].update(backup_output+'\n\n', append=True, visible=True)


def patch_game():
    if(get_Offsets(current_game)):        
        make_target_copy(current_game)
        print("+++++++++++++++")
        patch_Offsets(current_game)
        window['Restore'].update(visible=True)
    else:
        output = "Target hex patterns not found! Game might already be patched?"
        window['-OUTPUT_BOX-'].update(output+'\n\n', append=True, visible=True)


def patch_Offsets(appInfo):
    global path_to_patcher_exe

    offset_patches = []

    for offset in appInfo["patch_details"]:
        for x in offset[2]:
            foo = re.sub(r'.{4}', '\\g<0>,', (offset[1].decode('ascii')).replace("\\x",'0x'))
            bar = x+"="+foo[0:-1]
            offset_patches.append(bar)

    #bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    #path_to_patcher_exe = os.path.abspath(os.path.join(bundle_dir,'hexalter.exe'))

    print('\n\n')
    print([str(path_to_patcher_exe)] + [appInfo["target_file_path"]] + [offset_patches][0])
    #sys.exit()
    result = subprocess.run([str(path_to_patcher_exe)] + [appInfo["target_file_path"]] + [offset_patches][0], capture_output=True)
    print(result.stdout.decode())
    output = backup_output+'\n\n'+result.stdout.decode()+"'{}' file was patched for {}".format(appInfo['target_file'], appInfo['name'])
    window['-OUTPUT_BOX-'].update(output+'\n\n', append=True, visible=True)
    return 1


def make_target_copy(appInfo):
    global backup_output

    backuppath = Path(
        "./backups/{}/{}".format(appInfo["appID"], appInfo["target_file"]))
    try:
        os.makedirs(os.path.dirname(
            Path(backuppath)))
        shutil.copy2(
            appInfo["target_file_path"], backuppath)
        backup_output = ("Made a backup of unpatched file '{}' for {} in the backups folder:\n{}".format(
            appInfo["target_file"], appInfo["name"], backuppath))
        print(backup_output)
        with open(Path("./backups/{}/{}.txt".format(appInfo["appID"], appInfo["name"])), 'w') as fp:
            fp.write("This folder has the original backup of '{}' file for {}".format(
                appInfo['target_file'], appInfo["name"]))
        # window['-OUTPUT_BOX-'].update(output)

    except FileExistsError:
        backup_output = "Backup file already exists! Skipping backup step!"
        # window['-OUTPUT_BOX-'].update(output)



def setGameEntry(appInfo):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_help = os.path.abspath(os.path.join(bundle_dir,'games.json'))
    data = openJSON(path_to_help)
    appInfo["target_file_path"] = Path(str(appInfo["install_path"]) + data[appInfo["appID"]]["local_path"])
    appInfo["target_file"] = data[appInfo["appID"]]["target_file"]
    appInfo["target_file"] = data[appInfo["appID"]]["target_file"]
    appInfo["description"] = data[appInfo["appID"]]["description"]
    try:
        match selected_aspect_ratio:
            case '21:9 (3440x1440)':
                appInfo['apect_ratio_hex_patches'] = data[appInfo["appID"]]["3440_1440_hex_aspect_ratio_pattern"]
            case '21:9 (2560x1080)':
                appInfo['apect_ratio_hex_patches'] = data[appInfo["appID"]]["2560_1080_hex_aspect_ratio_pattern"]
            case '21:9 (3840x1600)':
                appInfo['apect_ratio_hex_patches'] = data[appInfo["appID"]]["3840_1600_hex_aspect_ratio_pattern"]
            case _:
                print("No matching aspect ratio was found!")
                sys.exit()
    except KeyError:
        print("KEYERROR!")
        sys.exit()


def get_Offsets(appInfo):

    with open(appInfo["target_file_path"], "rb") as f:
        data = f.read()
    
    apect_ratio_hex_patches = appInfo["apect_ratio_hex_patches"]
    nested_list = ast.literal_eval(apect_ratio_hex_patches)
    two_d_array = [[str(val) for val in sublist] for sublist in nested_list]

    patch_details = []
    for uw_patcher in two_d_array:
        patches = []
        for x in uw_patcher:
            hex_string = x.replace(" ", "").lower()
            hex_literal_string = "".join([f"\\x{hex_string[i:i+2]}" for i in range(0, len(hex_string), 2)])
            hex_literal_string = bytes(hex_literal_string, "utf-8")
            patches.append(hex_literal_string)
        patch_details.append(patches)
    
    appInfo["patch_details"] = patch_details

    offsets = []
    for x in appInfo["patch_details"]:
        patch = []
        i = 0
        while True:
            offset = data.find(x[0].decode('unicode-escape').encode('ISO-8859-1'), i)
            if offset == -1:
                break
            patch.append(hex(offset))
            i = offset + 1
        offsets.append(patch)
        x.append(patch)
        
    empty_array_counter = 0
    for array in offsets:
        if(array == []):
            empty_array_counter += 1

    if (len(offsets) == empty_array_counter):
        return 0
    else:
        return 1


def select_Game_GUI(values):
    global current_game

    window['-OUTPUT_BOX-'].update('')
    window['-OUTPUT_BOX-'].update('')

    pattern = r"\(([^()]+)\)[^()]*$"
    appID = re.findall(pattern, values['-LIST-'][0])[0]
    current_game = get_selected_game(appID)
    window['-CURRENT_GAME-'].update("{} ({}):\n'{}'".format(current_game['name'], 
                                                                   current_game['appID'],
                                                                   current_game['install_path']),
                                                                   font=(15))
    window['Patch'].update(visible=True)

    setGameEntry(current_game)
    backup_path = Path("./backups/{}/{}".format(current_game["appID"], current_game["target_file"]))
    if (backup_path.is_file()):
        window['Restore'].update(visible=True)
    else:
        window['Restore'].update(visible=False)

    #print(current_game)
    for key in current_game:
        print(key+" : "+str(current_game[key]))
    
    try:
        window['-DESCRIPTION-'].update(current_game['description'],
                                       background_color="red", text_color="white")
    except KeyError:
        window['-DESCRIPTION-'].update('')



def resetGUI(values):
    global steam_lib_filepath
    window['-OUTPUT_BOX-'].update('', background_color=('#2C2825'), text_color=('#FDCB52'))
    window['-CURRENT_GAME-'].update('')
    window['-DESCRIPTION-'].update('', background_color=('#2C2825'), text_color=('#FDCB52'))
    window['Patch'].update(visible=False)
    window['Restore'].update(visible=False)
    window['-LIST-'].update(values=[])
    steam_lib_filepath = Path(values['-STEAM_LIB_FILEPATH-'])
    if(open_VDF()):
        get_steam_apps()
        get_app_mainifests()
        filter_apps()
        window['-LIST-'].update(values=[filtered_apps], visible=True)


def get_steam_apps():
    global steam_paths
    global steam_apps

    window['-OUTPUT_BOX-'].update("", background_color=('#2C2825'), text_color=('#FDCB52'))

    steam_paths = []
    steam_apps = []
    for library in steam_libraries:
        path = steam_libraries[library]['path']
        steam_paths.append(path)
        for appID in steam_libraries[library]['apps']:
            steam_apps.append({"appID": appID, "library": path})


    # Manually search all appmanifest_xxx.acf files at each Steam library location
    # for some reason, not all installed games are written to libraryfolders.vdf
    for library in steam_libraries:
        path = steam_libraries[library]["path"]
        manifest_path = Path(path + "/steamapps")
        directory_list = os.listdir(manifest_path)
        for files in directory_list:
            if (re.match("^appmanifest_.*\.acf$", files)):
                appID = re.sub("appmanifest_|\.acf", "", files)
                app = {"appID": appID, "library": path}
                if app not in steam_apps:
                    steam_apps.append(app)


def open_VDF():
    global steam_lib_filepath
    global steam_libraries
    if(steam_lib_filepath == None):
        return
    try:
        steam_libraries = vdf.parse(open(steam_lib_filepath))
        steam_libraries = steam_libraries["libraryfolders"]
        return 1
    except:
        window['-OUTPUT_BOX-'].update("Not a valid 'steamlibrary.vdf' file!")
        steam_libraries = None
        return 0


def get_app_mainifests():
    for app in steam_apps:
        try:
            path_to_game_manifest = Path(app["library"] +
                                    "/steamapps/appmanifest_{}.acf".format(app["appID"]))
            game_manifest = vdf.parse(open(path_to_game_manifest))
            path_to_game_files = Path(app["library"] +
                                    "/steamapps/common/"+game_manifest["AppState"]["installdir"])
            app["name"] = game_manifest["AppState"]["name"]
            app["name"] = re.sub(
                r'[^A-Za-z0-9`~!@#$%^&*()-_=+;:\'\"\,.<>/?\{\} ]+', '', app["name"])
            app["install_path"] = path_to_game_files
        except:
            print("Game manifest not found for {}, game was probably uninstalled?".format(app['appID']))
            steam_apps.remove(app)


def filter_apps():
    global filtered_apps

    bundle_dir = getattr(
        sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_help = os.path.abspath(os.path.join(bundle_dir, 'games.json'))
    patch_list_dictionary = openJSON(path_to_help)

    patch_list = list(patch_list_dictionary.keys())
    filtered_apps = []
    for game in steam_apps:
        if game["appID"] in patch_list:
            filtered_apps.append("{}  ({})".format(game["name"], game["appID"]))


def openJSON(file_path):   
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def get_selected_game(appID):
    for game in steam_apps:
        if (appID == game["appID"]):
            return game


def main():
    # Find default Steam libraryfolder.vdf file and attempt to open it
    get_steam_lib_filepath()
    open_VDF()

    # Start GUI loop, if VDF not found, ask until valid VDF fed in
    createGUI()
    guiLoop()

if __name__=="__main__":
    main()
