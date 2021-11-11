#!/usr/bin/env python3
"""
This is the main file that contains the web server.
It uses flask.
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from db import DataBase, Post
from config import read_config_file
import sys

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
    db = DataBase(server_config)

# --------------------------------- REST API --------------------------------- #

@app.route("/<string:board>/", methods=['POST'])
@limiter.limit('5 per 1 seconds')
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
        return "Error, post too long. Max size = "+str(board_config["max_post_size"])+".", 400
    # TODO: Check inside of the content for ANSI codes
    
    # Posting
    postOK = db.auto_post(board, content, replyTo)
    if postOK:
        return "OK", 200
    else:
        return "Not OK", 400


@app.route("/<string:board>/", methods=['GET'])
@limiter.limit("5 per 1 second")
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
    app.run()

