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
            "/home/{}/.local/share/Steam/steamapps/libraryfolders.vdf".format(os.getlogin()))
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
            steam_library_filepath = None


    sg.theme('DarkAmber')   # Add a touch of color
    # All the stuff inside your window.
    layout = [
        [sg.T('Ultrawider',
              font=('Arial Bold', 25),
              size=20,
              expand_x=True,
              justification='center')],
        [sg.Text("Steam Library File", font=(15)),
         sg.In(key="-STEAM_LIBRARY_FILEPATH-", default_text=steam_library_filepath,size=(55, 1), font=(15),
               change_submits=True, enable_events=True), sg.FileBrowse()],
        [sg.T(key='-OUTPUT_BOX-', font=(15))]
    ]

    # Create the Window
    window = sg.Window('', layout, finalize=True)
    

def guiLoop():
    global window
    global steam_library_filepath

    if(steam_library_filepath != None):
        get_steam_apps()
    else:
        window['-OUTPUT_BOX-'].update("Error! Find the \"libraryfolders.vdf\" file under <path_to_steam>/Steam/steamapps/", 
        background_color="red", text_color="white")

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()            
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if event == '-STEAM_LIBRARY_FILEPATH-':
            window['-OUTPUT_BOX-'].update('')
            steam_library_filepath = Path(values['-STEAM_LIBRARY_FILEPATH-'])
            if(open_VDF(steam_library_filepath)):
                get_steam_apps()
    window.close()


def get_steam_apps():
    window['-OUTPUT_BOX-'].update("Finding your installed games!", background_color=('#2C2825'), text_color=('#FDCB52'))


def open_VDF(path_vdf_file):
    global steam_libraries
    try:
        steam_libraries = vdf.parse(open(path_vdf_file))
        steam_libraries = steam_libraries["libraryfolders"]
        return 1
    except:
        window['-OUTPUT_BOX-'].update('Not a valid VDF file!')
        steam_libraries = None
        return 0


def main():
    get_steam_library_filepath()
    createGUI()
    guiLoop()

if __name__=="__main__":
    main()
