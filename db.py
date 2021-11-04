#!/usr/bin/env python3
"""
This file contains what is needed to interrac with the database of all posts.
As of now, for testing purpuse, the posts are stored in RAM and backed-up in a
JSON file. But this will have to be replaced with a proper database in the future.
"""

from dataclasses import dataclass

@dataclass
class Post:
    """
    This class is used to represent a single post.
    """
    ID: int
    replyTo: int
    content: str


# The database containing all the posts. As of now, for testing purpuse,
# it is initialised at startup.
class DataBase:
    def __init__(self):
        self.db = {'t' : [], 'n' : []}

    def __str__(self):
        return str(self.db)

    # Return the next valid ID for a board
    def next_id(self, board):
        return len(self.db[board]) + 1

    # Tries to append a new post to a board. If it can be done, return True
    def new_post(self, board, post):
        if len(self.db[board]) + 1 == post.ID: # TODO: test for replyTo's value
            self.db[board].append(post)
            return True
        else:
            return False

    # Make a new post with a comment and a replyTo and automaticaly choose the
    # righ ID. Returns the same value as new_post
    def auto_post(self, board, content, replyTo):
        ID = self.next_id(board)
        post = Post(ID = ID, content = content, replyTo = replyTo)
        return self.new_post(board, post)

# ---------------------------------- Testing --------------------------------- #

print('potate')
if __name__ == '__main__':
    db = DataBase()
    for i in range(10):
        db.auto_post('t', str(i), 0)
    print(db)

