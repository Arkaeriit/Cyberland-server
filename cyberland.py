#!/usr/bin/env python3
"""
This is the main file that contains the web server.
It uses flask.
"""

from flask import Flask, request, jsonify, render_template, url_for, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from db import DataBase
from config import read_config_file
from anti_spam import manage_request, get_IP, try_to_filter, manage_request_ret
import sys
import json
import random
from flask_cors import CORS

# -------------------------- Preparing server's state ------------------------ #

if __name__ == '__main__':
    app = Flask(__name__)
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["5 per seconds"]
    )
    CORS(app)
    config_OK, server_config = read_config_file("config.json")
    if not config_OK:
        print("Unable to read configuration.")
        sys.exit(1)
    db = DataBase(server_config, "db")
    LOG_FILE = "cyberland_log"

# ------------------------------- Default pages ------------------------------ #

def render_txt(filename):
    "Render a txt file from the `txt` folder."
    with open("txt/" + filename, "r") as f:
        txt = f.read()
    response = make_response(txt, 200)
    response.mimetype = "text/plain"
    return response

@app.route("/", methods=['GET'])
def root():
    all_boards = list(server_config.keys())
    example_board = random.choice(all_boards)
    return render_template("index.html", example_board = example_board)

@app.route("/tut.txt/", methods=['GET'])
@app.route("/tut.txt", methods=['GET'])
def tut_txt():
    return render_txt("tut.txt")

@app.route("/banner.txt/", methods=['GET'])
@app.route("/banner.txt", methods=['GET'])
def banner_txt():
    return render_txt("banner.txt")

@app.route("/config/", methods=['GET'])
@app.route("/config", methods=['GET'])
def get_config():
    "This page returns a JSON of the config of all boards."
    return jsonify(server_config), 200

@app.route("/status/", methods=['GET'])
@app.route("/status", methods=['GET'])
@app.route("/length/", methods=['GET'])
@app.route("/length", methods=['GET'])
def get_lengths():
    "This page returns the number of posts in each boards."
    ret = {}
    for k in db.db.keys():
        ret[k] = len(db.db[k])
    return jsonify(ret)

@app.route("/boards/", methods=['GET'])
@app.route("/boards", methods=['GET'])
def get_boards():
    "Returns a description slimmer than /status but longer than /config."
    ret = []
    for server in server_config:
        print(server)
        serv_formated = {
                "slug":      server_config[server]["name"],
                "name":      server_config[server]["long_name"],
                "charLimit": server_config[server]["max_post_size"],
                "post":      len(db.db[server_config[server]["name"]])}
        ret.append(serv_formated)
    return jsonify(ret)

# --------------------------------- REST API --------------------------------- #

@app.route("/<string:board>/", methods=['POST'])
@app.route("/<string:board>", methods=['POST'])
def posting(board, detail:bool=False):
    # Checking if board exists
    try:
        board_config = server_config[board]
    except KeyError:
        return "Error, requested board does not exits.", 400

    # Getting and testing the arguments
    content = request.form.get('content')
    replyTo = request.form.get('replyTo')
    if not replyTo or replyTo == 'null':
        replyTo = '0'
    if not replyTo.isdigit():
        return "Error, replyTo is not a number nor null!", 400
    replyTo = int(replyTo)
    if not content:
        return "Error, no content provided.", 400
    if len(content) > board_config["max_post_size"]:
        return "Error, post too long. Max size = "+str(board_config["max_post_size"])+", size of the message = "+str(len(content))+".", 400

    # Checking for ANSI codes
    if not board_config["enable_ansi_code"]:
        for i in content:
            chr_int = ord(i)
            if chr_int < 32 and i != "\n" and i != "\r" and i != "\t":
                return "Error, unauthorized char. ANSI code are not allowed.", 400

    # Checking for spam
    OK_to_post, timeout = manage_request(request)
    if OK_to_post == manage_request_ret["Limit"]:
        return "Error, you must wait " + str(timeout) + " ms before posting again.", 400
    elif OK_to_post == manage_request_ret["First_time"]:
        return "As it is your first time posting, you must wait " + str(timeout) + " ms before posting.", 400

    # Checking for forbidden words
    language_OK = try_to_filter(content, request)
    if not language_OK:
        return "Clean your mouth with soap!", 400
    
    # Posting
    postOK, id = db.auto_post(board, content, replyTo)
    if postOK:
        with open(LOG_FILE, "a") as f:
            f.write(str(get_IP(request))+", "+board+", "+str(id)+"\n")
        if detail:
            return "OK", 200, id
        else:
            return "OK", 200
    else:
        return "Not OK", 400


@app.route("/<string:board>/", methods=['GET'])
@app.route("/<string:board>", methods=['GET'])
def reading(board):
    # Checking if board exists
    try:
        board_config = server_config[board]
    except KeyError:
        return "Error, requested board does not exits.", 400

    # Validated request form
    num = request.args.get('num')
    thread = request.args.get('thread')
    offset = request.args.get('offset')
    if not num:
        num = '100' #TODO: config
    if num.isdigit():
        num_int = int(num)
    else:
        return "Num parameter is not a number", 400
    if not offset:
        offset = '0'
    if not offset.isdigit():
        return "Offset parameter is not a number", 400
    offset = int(offset)

    # Limiting reply size
    if not thread:
        if board_config["max_replies_no_thread"] != 0:
            if board_config["max_replies_no_thread"] < num_int:
                num_int = board_config["max_replies_no_thread"]
    else:
        if board_config["max_replies_thread"] != 0:
            if board_config["max_replies_thread"] < num_int:
                num_int = board_config["max_replies_thread"]

    # Reading last posts
    if not thread:
        reply = db.get_last_posts(board, num_int + offset)
        return jsonify(reply[offset:]), 200
    # Reading part of a thread
    else:
        if thread.isdigit():
            thread_int = int(thread)
        elif thread == "null":
            thread_int = 0
        else:
            return "Thread parameter is not a number", 400
        OP, post_OK = db.get_post(board, thread_int)
        if not post_OK:
            return "Error, no such thread as " + thread, 400
        replies = db.get_first_replies(board, num_int-1+offset, thread_int)
        reply = [OP] + replies
        return jsonify(reply[offset:]), 200


# ---------------------------- Running the server ---------------------------- #

if __name__ == '__main__':
    app.run(port = 8901)

