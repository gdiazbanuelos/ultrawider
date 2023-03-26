# define the hex string to convert
hex_string = "39 8E E3 3F".replace(" ", "")

# convert the hex string to a hex literal string
hex_literal_string = "".join([f"\\x{hex_string[i:i+2]}" for i in range(0, len(hex_string), 2)])
print(hex_literal_string)