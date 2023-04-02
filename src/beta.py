import PySimpleGUI as sg
import vdf
import os
import sys
from sys import platform
from pathlib import Path
import re

steam_lib_filepath = None
steam_libraries = None

steam_paths = None
steam_apps = None

window = None


# Find all installed Steam Games
#   Find libfolders.vdf, search default location for OS
#       If not in default location, prompt to manually input location libfolders.vdf


def get_steam_lib_filepath():
    global steam_lib_filepath
    global steam_libraries

    # Try default Steam install location
    if platform == "linux" or platform == "linux2":
        steam_lib_filepath = Path(
            "/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
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
        if (steam_lib_filepath.exists()):
            print("Found default Steam '{}' file!".format(steam_lib_filepath.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_lib_filepath.name))
            steam_lib_filepath = None
            return


def createGUI():
    global window
    global steam_lib_filepath

    sg.theme('DarkAmber')   # Add a touch of color
    # All the stuff inside your window.
    layout = [
        [sg.T('Ultrawider',
              font=('Arial Bold', 25),
              size=20,
              expand_x=True,
              justification='center')],
        [sg.Text("Steam Library File", font=(15)),
         sg.In(key="-STEAM_LIB_FILEPATH-", default_text=steam_lib_filepath,size=(55, 1), font=(15),
               change_submits=True, enable_events=True), sg.FileBrowse()],
        [sg.T(key='-OUTPUT_BOX-', font=(15))]
    ]

    # Create the Window
    window = sg.Window('', layout, finalize=True)
    

def guiLoop():
    global window
    global steam_lib_filepath

    if(steam_lib_filepath != None):
        get_steam_apps()
    else:
        window['-OUTPUT_BOX-'].update("Error! Find the \"libraryfolders.vdf\" file under <path_to_steam>/Steam/steamapps/", 
        background_color="red", text_color="white")

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()            
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if event == '-STEAM_LIB_FILEPATH-':
            window['-OUTPUT_BOX-'].update('')
            steam_lib_filepath = Path(values['-STEAM_LIB_FILEPATH-'])
            if(open_VDF()):
                get_steam_apps()
    window.close()


def get_steam_apps():
    global steam_paths
    global steam_apps

    window['-OUTPUT_BOX-'].update("Finding your installed games!", background_color=('#2C2825'), text_color=('#FDCB52'))

    steam_paths = []
    steam_apps = []
    for library in steam_libraries:
        path = steam_libraries[library]['path']
        steam_paths.append(path)
        for appID in steam_libraries[library]['apps']:
            steam_apps.append({
                "appID": appID,
                "library": path
            })
    

    # Manually search all appmanifest_xxx.acf files at each Steam library location
    # for some reason, not all installed games are written to libraryfolders.vdf
    for library in steam_libraries:
        steam_lib_path = steam_libraries[library]["path"]
        manifest_path = Path(steam_lib_path + "/steamapps")
        directory_list = os.listdir(manifest_path)
        for files in directory_list:
            if (re.match("^appmanifest_.*\.acf$", files)):
                gameID = re.sub("appmanifest_|\.acf", "", files)
                gameEntry = {"appID": gameID, "library": steam_lib_path}
                if gameEntry not in steam_apps:
                    steam_apps.append(gameEntry)


    print(steam_paths)

    for app in steam_apps:
        print(app)


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


def main():
    get_steam_lib_filepath()
    open_VDF()
    createGUI()
    guiLoop()

if __name__=="__main__":
    main()
