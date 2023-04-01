import PySimpleGUI as sg
import vdf
import os
import sys
from sys import platform
from pathlib import Path

steam_library_filepath = None
steam_libraries = None
window = None

# Find all installed Steam Games
#   Find libraryfolders.vdf, search default location for OS
#       If not in default location, prompt to manually input location libraryfolders.vdf


def get_steam_library_filepath():
    global steam_library_filepath
    global steam_libraries


    # Try default Steam install location
    if platform == "linux" or platform == "linux2":
        steam_library_filepath = Path(
            "f/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
        if (steam_library_filepath.exists()):
            print("Found default Steam '{}' file!".format(steam_library_filepath.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_library_filepath.name))
            steam_library_filepath = None
            return
    elif platform == "darwin":
        # OS X
        pass
    elif platform == "win32":
        steam_library_filepath = Path(
            'C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf')
        if (steam_library_filepath.exists()):
            print("Found default Steam '{}' file!".format(steam_library_filepath.name))
        else:
            print("Failed to find default Steam '{}' file!".format(steam_library_filepath.name))
            steam_library_filepath = None
            return

    steam_libraries = vdf.parse(open(steam_library_filepath))
    steam_libraries = steam_libraries["libraryfolders"]


def createGUI():
    global window
    global steam_library_filepath

    if(steam_library_filepath == None):
            steam_library_filepath = "Locate your 'libraryfolders.vdf' under ~/Steam/steamapps "


    sg.theme('DarkAmber')   # Add a touch of color
    # All the stuff inside your window.
    layout = [
        [sg.T('Ultrawider',
              font=('Arial Bold', 20),
              size=20,
              expand_x=True,
              justification='center')],
        [sg.Text("Steam Library File"),
         sg.In(key="-STEAM_LIBRARY_FILEPATH-", default_text=steam_library_filepath,size=(55, 1), change_submits=True),
         sg.FileBrowse()],
        [sg.T(key='-STEAM_LIBRARY_FILEPATH_ERROR-', visible=False)]
    ]

    # Create the Window
    window = sg.Window('Ultrawider', layout)
    

def updateGUI():
    global window

    event, values = window.read()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if event == '-STEAM_LIBRARY_FILEPATH-':
            print(values['-STEAM_LIBRARY_FILEPATH-'])
    window.close()

def main():
    get_steam_library_filepath()
    createGUI()

    updateGUI()

if __name__=="__main__":
    main()
