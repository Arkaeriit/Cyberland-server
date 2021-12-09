#!/usr/bin/env python3
"""
This file contains the code needed to read the configuration file and verify
its content.
"""

import json

def json_to_dic(filename):
    """This function opens a file and use reads it as JSON. This does not much
    more than json.load but I wanted to make it in a separate function if I
    even need to do error checking. As of now, there is no error checking 
    because this is very low priority as this function should only be called
    once at the beginning of the program."""
    with open(filename, "r") as f:
        file_content = f.read()
    dic = json.loads(file_content)
    return dic

# This dictionary is a reference of all the field expected in the config
# and their type
config_fields = [
        {"name": "name",                  "type": str,  "optional": False},
        {"name": "long_name",             "type": str,  "optional": True,  "default": ""},
        {"name": "description",           "type": str,  "optional": True,  "default": ""},
        {"name": "max_post_size",         "type": int,  "optional": False},
        {"name": "enable_ansi_code",      "type": bool, "optional": False},
        {"name": "max_replies_thread",    "type": int,  "optional": True,  "default": 0},
        {"name": "max_replies_no_thread", "type": int,  "optional": True,  "default": 0},
]

def format_board_config(dic):
    """This function tells if the content of the dictionary given as
    input is compliant with the info in "config_fields".
    It also generates a dictionary with correct type casings.
    It returns as first value, a boolean telling that no error
    were found, then a dictionary with correct converions for the config
    and finaly, an error message.
    It is meant to be run on the config for a board, not the config for the
    whole server."""
    ret = {}
    for fields in config_fields:
        try:
            config_value = dic[fields["name"]]
            try:
                ret[fields["name"]] = fields["type"](config_value)
            except ValueError:
                return False, ret, "Error in the type of "+fields["name"]+"."
        except KeyError:
            if fields["optional"]:
                ret[fields["name"]] = fields["default"]
            else:
                return False, ret, "Error, non optional value "+fields["name"]+" is missing."
    return True, ret, "No errors."

def format_server_config(server_config_list):
    """Formats check the configuration for each board in the whole server.
    Returns an boolean who tell that no error happend and also a dictionary
    whose keys are the name of board and whose value are the configuration
    dictionaries for the board."""
    ret = {}
    for board in server_config_list:
        board_OK, board_config, error_msg = format_board_config(board)
        if not board_OK:
            try:
                name = board["name"]
                print("Error in board "+str(name)+":\n"+error_msg)
            except KeyError:
                print("A board have no name.")
            return False, ret
        ret[board_config["name"]] = board_config
    return True, ret

def read_config_file(filename):
    "Reads a config file and returns the same things as format_server_config."
    config_OK, server_config = format_server_config(json_to_dic(filename))
    return config_OK, server_config

# ----------------------------------- Test ----------------------------------- #

if __name__ == '__main__':
    print(json_to_dic("config.json"))
    print("\n--------------\n")
    print(format_server_config(json_to_dic("config.json")))

