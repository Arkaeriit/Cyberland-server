#!/usr/bin/env python3
"""
This is the main file that contains the web server.
It uses flask.
"""

from flask import Flask, request, jsonify, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from db import DataBase
from config import read_config_file
from anti_spam import manage_request, get_IP
import sys
import json
import random

# -------------------------- Preparing server's state ------------------------ #

if __name__ == '__main__':
    app = Flask(__name__)
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    config_OK, server_config = read_config_file("config.json")
    if not config_OK:
        print("Unable to read configuration.")
        sys.exit(1)
    db = DataBase(server_config, "db.json")
    LOG_FILE = "cyberland_log"

# ------------------------------- Default pages ------------------------------ #

@app.route("/", methods=['GET'])
def root():
    all_boards = list(server_config.keys())
    example_board = random.choice(all_boards)
    return render_template("index.html", example_board = example_board)

@app.route("/config/", methods=['GET'])
@app.route("/config", methods=['GET'])
@limiter.limit('1 per 5 seconds')
def get_config():
    "This page returns a JSON of the config of all boards."
    return jsonify(server_config), 200

@app.route("/status/", methods=['GET'])
@app.route("/status", methods=['GET'])
@app.route("/length/", methods=['GET'])
@app.route("/length", methods=['GET'])
@limiter.limit('1 per 1 seconds')
def get_lengths():
    "This page returns the number of posts in each boards."
    ret = {}
    for k in db.db.keys():
        ret[k] = len(db.db[k])
    return jsonify(ret)

# --------------------------------- REST API --------------------------------- #

@app.route("/<string:board>/", methods=['POST'])
@app.route("/<string:board>", methods=['POST'])
@limiter.limit('1 per 1 seconds')
@limiter.limit('100 per 30 minutes')
def posting(board):
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
    if not OK_to_post:
        return "Error, you must wait " + str(timeout) + " ms before posting again.", 400
    
    # Posting
    postOK, id = db.auto_post(board, content, replyTo)
    if postOK:
        with open(LOG_FILE, "a") as f:
            f.write(str(get_IP(request))+", "+board+", "+str(id)+"\n")
        return "OK", 200
    else:
        return "Not OK", 400


@app.route("/<string:board>/", methods=['GET'])
@app.route("/<string:board>", methods=['GET'])
@limiter.limit("5 per 1 second")
@limiter.limit('100 per 10 minutes')
def reading(board):
    # Checking if board exists
    try:
        board_config = server_config[board]
    except KeyError:
        return "Error, requested board does not exits.", 400

    # Validated request form
    num = request.args.get('num')
    thread = request.args.get('thread')
    if not num:
        num = '100' #TODO: config
    if num.isdigit():
        num_int = int(num)
    else:
        return "Num parameter is not a number", 400

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
        reply = db.get_last_posts(board, num_int)
        return jsonify(reply), 200
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
        replies = db.get_first_replies(board, num_int-1, thread_int)
        reply = [OP] + replies
        return jsonify(reply), 200


# ---------------------------- Running the server ---------------------------- #

if __name__ == '__main__':
    app.run(port = 8901)

