#!/usr/bin/env python3
"""
This is the main file that contains the web server.
It uses flask.
"""

from flask import Flask, request
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
@limiter.limit('1 per 1 seconds')
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
@limiter.limit("1 per 1 second")
def reading(board):
    return "TODO", 400

# ---------------------------- Running the server ---------------------------- #

if __name__ == '__main__':
    app.run()

