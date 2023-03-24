import re

string = "This is a sample string with multiple (ID:12345) patterns (ID:67890)"
pattern = r"\(ID:\d+\)"

result = re.sub(pattern, lambda match: str(max(map(int, re.findall(r'\d+', match.group())))), string)

print(result)
