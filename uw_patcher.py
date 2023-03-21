import sys
import subprocess
import json

target_file = None
search_pattern = None
patch_pattern = None

# patterns from cmd line are the positions
# ie. search pattern n is in the nth position
search_pattern_hex = [b"\x39\x8e\xe3\x3f",b"\x55\x55\x15\x40"]

# patterns from cmd line are the positions
# ie. patch pattern n is in the nth position
patch_pattern_hex = ["=0xCD,0x90,0x18,0x40", "=0x60,0xE5,0x18,0x40", "=0x8E,0xE3,0x18,0x40"]

def getOffsets(): 
    global target_file
    global search_pattern
    global patch_pattern
    target_file = sys.argv[1]

    #TODO create datebase to autoset these
    search_pattern = getGameEntry(sys.argv[2])[0]
    patch_pattern = getGameEntry(sys.argv[2])[1]

    with open(target_file, "rb") as f:
        data = f.read()

    pattern = search_pattern_hex[int(search_pattern)]
    
    offsets = []
    i = 0
    while True:
        offset = data.find(pattern, i)
        if offset == -1:
            break
        offsets.append(hex(offset))
        i = offset + 1

    if len(offsets) == 0:
        print("Pattern not found.")
    else:
        return offsets


def patchOffsets(offsets):
    offset_patches = []
    for offset in offsets:
        offset_patches.append(offset+patch_pattern_hex[int(patch_pattern)])

    c_script_path = "./hexalter"
    result = subprocess.run([c_script_path] + [target_file] + [offset_patches][0], capture_output=True)
    print(result.stdout.decode())


def openJSON(file_path):   
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def getGameEntry(steamAppID):
    data = openJSON("games.json")
    return [data[steamAppID]["search_pattern"], data[steamAppID]["patch_pattern"]]


if __name__== "__main__":
    if(len(sys.argv) != 3):
        print("Usage: python3 this.py <file_path> <SteamAppID>")
        sys.exit()

    offsets = getOffsets()
    patchOffsets(offsets)
