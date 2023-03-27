import re
import subprocess
import json
from pathlib import Path
import os
import sys
import ast


def getOffsets(appInfo):

    with open(appInfo["absolute_path"], "rb") as f:
        data = f.read()
    
    test = appInfo["3440_1440_hex_aspect_ratio_pattern"]
    nested_list = ast.literal_eval(test)
    two_d_array = [[str(val) for val in sublist] for sublist in nested_list]

    bars = []
    for uw_patcher in two_d_array:
        foo = []
        for x in uw_patcher:
            hex_string = x.replace(" ", "").lower()
            hex_literal_string = "".join([f"\\x{hex_string[i:i+2]}" for i in range(0, len(hex_string), 2)])
            hex_literal_string = bytes(hex_literal_string, "utf-8")
            foo.append(hex_literal_string)
        bars.append(foo)
    
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
        
    y = 0
    for x in offsets:
        if(x == []):
            y+=1

    if (len(offsets) == y):
        return 0
    else:
        return 1


def patchOffsets(appInfo):
    offset_patches = []

    for offset in appInfo["patch_details"]:
        for x in offset[2]:
            foo = re.sub(r'.{4}', '\\g<0>,', (offset[1].decode('ascii')).replace("\\x",'0x'))
            bar = x+"="+foo[0:-1]
            offset_patches.append(bar)

    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_patcher_exe = os.path.abspath(os.path.join(bundle_dir,'hexalter.exe'))

    #print([str(path_to_patcher_exe)] + [appInfo["absolute_path"]] + [offset_patches][0])

    result = subprocess.run([str(path_to_patcher_exe)] + [appInfo["absolute_path"]] + [offset_patches][0], capture_output=True)
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
    appInfo["absolute_path"] = Path(str(appInfo["path"]) + data[appInfo["appID"]]["local_path"])
    appInfo["target_file"] = data[appInfo["appID"]]["target_file"]
    appInfo["3440_1440_hex_aspect_ratio_pattern"] = data[appInfo["appID"]]["3440_1440_hex_aspect_ratio_pattern"]
    try:
        appInfo["3440_1440_hex_fov_pattern"] = data[appInfo["appID"]]["3440_1440_hex_fov_pattern"]
    except KeyError:
        appInfo["3440_1440_hex_fov_pattern"] = None