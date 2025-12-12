import json
import sys
import os

# Add the parent directory (myproject/) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils  # now you can use utils.whatever()


with open("data/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

while True:
    i = utils.normalize_text(input("input: "))
    r = utils.normalize_text(input("response: "))
    if i == "quit" or r == "quit":
        break
    data.append({"i": i, "r": r})
    

with open("data/data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

