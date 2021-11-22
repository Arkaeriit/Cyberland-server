#!/usr/bin/env python3
"""
This file contains what is needed to interact with the database of all posts.
As of now, for testing purpose, the posts are stored in RAM and backed-up in a
JSON file. But this will have to be replaced with a proper database in the future.
"""

import json
import time

class DataBase:
    """The database containing all the posts. As of now, for testing purpuse,
    it is only an humble JSON file"""
    def __init__(self, server_config, db_filename):
        # Reading db file
        self.db_filename = db_filename
        try:
            with open(db_filename, "r") as db_f:
                self.db = json.load(db_f)
        except FileNotFoundError: # New server
            self.db = {}
        # Note: JSONDecodeError are considered fatal and not catched

        # Starting up new boards
        for k in server_config.keys():
            try:
                self.db[k]
            except KeyError:
                self.db[k] = [{"id": 0, "time": 0, "replyTo": 0, "content": server_config[k]["description"]}]

        # Pruning old boards from the DB
        to_pop = []
        for k in self.db.keys():
            try:
                server_config[k]
            except KeyError:
                to_pop.append(k)
        for k in to_pop:
            self.db.pop(k)

    def update_db(self):
        "Update the db JSON file with new content from the internal DB."
        with open(self.db_filename, "w") as db_f:
            json_str = json.dumps(self.db)
            db_f.write(json_str)

    def __str__(self):
        return str(self.db)

    def next_id(self, board):
        "Return the next valid ID for a board"
        return len(self.db[board])

    def new_post(self, board, post):
        "Tries to append a new post to a board. If it can be done, return True."
        if len(self.db[board]) == post["id"]: # TODO: test for replyTo's value
            self.db[board].append(post)
            post["time"] = int(time.time())
            self.update_db()
            return True
        else:
            return False

    def auto_post(self, board, content, replyTo):
        """Make a new post with a comment and a replyTo and automatically choose the
        right ID. Returns the same value as new_post."""
        id = self.next_id(board)
        post = {"id": id, "content": content, "replyTo": replyTo}
        return self.new_post(board, post)

    def get_last_posts(self, board, num):
        "Reads the db to find the last few posts."
        if num > len(self.db[board]):
            num = len(self.db[board])
        reply = []
        for i in range(len(self.db[board])-1, len(self.db[board])-num-1, -1):
            reply.append(self.db[board][i])
        return reply

    def get_post(self, board, id):
        """Returns a specific post by its ID.
        Also returns a boolean telling if the search was successful."""
        try:
            if self.db[board][id]["id"] == id: # Everything is well
                return self.db[board][id], True
            else:
                raise IndexError # Force a pass in the except block
        except IndexError:
            return None, False

    def get_first_replies(self, board, num, id):
        "Return the first few post replying to an other post."
        ret = []
        for i in self.db[board][id+1:-1]:
            if i["replyTo"] == id:
                ret.append(i)
                if len(ret) == num:
                    break
        return ret

# ---------------------------------- Testing --------------------------------- #

if __name__ == '__main__':
    from config import read_config_file
    config_OK, server_config = read_config_file("config.json")
    db = DataBase(server_config, "db.json")
    print('\n -- Testing posting -- \n')
    for i in range(10):
        db.auto_post('test', str(i), 0)
    print(db)
    print('\n -- Testing reading some posts -- \n')
    print(db.get_last_posts('test', 4))
    print(db.get_last_posts('test', 0))
    print(db.get_last_posts('test', 1))
    print(db.get_last_posts('test', 11))
    print(db.get_last_posts('test', 12))
    print('\n -- Testing reading post by ID -- \n')
    print(db.get_post('test', 4))
    print(db.get_post('test', -1))
    print(db.get_post('test', 100))
    print('\n -- Testing reading thread -- \n')
    print(db.get_first_replies('test', 4, 0))

