#!/usr/bin/env python3
"""
This is the main file that contains the web server.
It uses flask.
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from db import DataBase, Post

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
db = DataBase()

@app.route("/<string:board>/", methods=['POST'])
@limiter.limit('5 per 1 seconds')
def posting(board):
    # Getting and testing the arguments
    content = request.form.get('content')
    replyTo = request.form.get('replyTo')
    if not replyTo or replyTo == 'null':
        replyTo = '0'
    if not replyTo.isdigit():
        return "Error, replyTo is not a number nor null!", 400
    replyTo = int(replyTo)
    # TODO: validate the content against the board number
    
    postOK = db.auto_post(board, content, replyTo)
    if postOK:
        return "OK", 200
    else:
        return "Not OK", 400


@app.route("/<string:board>/", methods=['GET'])
@limiter.limit("5 per 1 second")
def reading(board):
    num = request.args.get('num')
    thread = request.args.get('thread')

    if not num:
        num = '100' #TODO: config
    if num.isdigit():
        num_int = int(num)
    else:
        return "Num parameter is not a number", 400

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

