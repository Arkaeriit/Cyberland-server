#!/usr/bin/env python3
"""
This small tool is ment to convert old single-file databases into
new multi-files databases.
"""

import json

with open("db.json", "r") as f_read:
    s = f_read.read()
    full_db = json.loads(s)
    for k in full_db.keys():
        json_str = json.dumps(full_db[k])
        with open("db/" + k + ".json", "w") as f_write:
            f_write.write(json_str)

