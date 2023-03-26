import subprocess
import json
from pathlib import Path
import os
import sys
import ast

target_file = None
search_pattern = None
patch_pattern = None

#TODO create dynamic patcher patterns from json

# patterns from cmd line are the positions
# ie. search pattern n is in the nth position
search_pattern_hex = [b"\x39\x8e\xe3\x3f",b"\x55\x55\x15\x40"]

# patterns from cmd line are the positions
# ie. patch pattern n is in the nth position
patch_pattern_hex = ["=0xCD,0x90,0x18,0x40", "=0x60,0xE5,0x18,0x40", "=0x8E,0xE3,0x18,0x40"]

def getOffsets(appInfo):

    #TODO dynamic parsing of JSON for patterns
    global target_file
    global search_pattern
    global patch_pattern

    target_file = appInfo["path"]

    #TODO create datebase to autoset these
    search_pattern = appInfo["search_pattern"]
    patch_pattern = appInfo["patch_pattern"]

    with open(target_file, "rb") as f:
        data = f.read()

    patterns = search_pattern_hex[int(search_pattern)]
    
    test = appInfo["219_3440_1440_hex_pattern"]
    nested_list = ast.literal_eval(test)
    two_d_array = [[str(val) for val in sublist] for sublist in nested_list]

    bars = []
    for uw_patcher in two_d_array:
        foo = []
        for x in uw_patcher:
            hex_string = x.replace(" ", "").lower()
            # convert the hex string to a hex literal string
            hex_literal_string = "".join([f"\\x{hex_string[i:i+2]}" for i in range(0, len(hex_string), 2)])
            hex_literal_string = bytes(hex_literal_string, "utf-8")
            
            foo.append(hex_literal_string)
        bars.append(foo)
    #print(bars)
    
    appInfo["patch_details"] = bars

    offsets = []
    for x in  appInfo["patch_details"]:
        foo = []
        i = 0
        while True:
            offset = data.find(x[0].decode('unicode-escape').encode('ISO-8859-1'), i)
            if offset == -1:
                break
            foo.append(hex(offset))
            i = offset + 1
        offsets.append(foo)
        x.append(foo)
        

    if len(offsets) == 0:
        return -1
    else:
        return 1


def patchOffsets(appInfo):
    offset_patches = []

    for offset in appInfo["patch_details"]:
        for x in offset[2]:
            print(x,offset[1])

    sys.exit()
    for offset in appInfo["patch_details"]:
        for x in offset[2]:
            offset_patches.append(offset+patch_pattern_hex[int(patch_pattern)])


    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_patcher_exe = os.path.abspath(os.path.join(bundle_dir,'hexalter.exe'))

    print([str(path_to_patcher_exe)] + [appInfo['local_path']] + [offset_patches][0])
    sys.exit()

    result = subprocess.run([str(path_to_help)] + [appInfo['local_path']] + [offset_patches][0], capture_output=True)
    print(result.stdout.decode())
    return 1


def openJSON(file_path):   
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def setGameEntry(appInfo):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_help = os.path.abspath(os.path.join(bundle_dir,'games.json'))
    data = openJSON(path_to_help)
    appInfo["path"] = Path(str(appInfo["path"]) + data[appInfo["appID"]]["local_path"])
    appInfo["target_file"] = data[appInfo["appID"]]["target_file"]
    appInfo["search_pattern"] = data[appInfo["appID"]]["search_pattern"]
    appInfo["patch_pattern"] = data[appInfo["appID"]]["patch_pattern"]
    appInfo["219_3440_1440_hex_pattern"] = data[appInfo["appID"]]["219_3440_1440_hex_pattern"]
