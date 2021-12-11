#!/usr/bin/env python3
"""
This small too is meant to compute the value of the bumpCount fields of post
and add it into an existing data base file.
The path of the data base file to update should be given as argument.
"""

import json
import sys
import os

with open(sys.argv[1], "r") as f:
    s = f.read()

db = json.loads(s)

for i in range(len(db)):
    if i != db[i]["id"]:
        print("Error, array not sorted by id.")
        os.exit(1)
    db[i]["bumpCount"] = 0
    try:
        db[db[i]["replyTo"]]["bumpCount"] += 1
    except:
        print(db[i])

with open(sys.argv[1], "w") as f:
    f.write(json.dumps(db))

