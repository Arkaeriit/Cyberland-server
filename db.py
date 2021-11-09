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
    id: int
    replyTo: int
    content: str


# The database containing all the posts. As of now, for testing purpuse,
# it is initialised at startup.
class DataBase:
    def __init__(self):
        self.db = {'t' : [Post(id = 0, replyTo = 0, content = "xxx")], 'n' : [Post(id = 0, replyTo = 0, content = "xxx")]}

    def __str__(self):
        return str(self.db)

    # Return the next valid ID for a board
    def next_id(self, board):
        return len(self.db[board])

    # Tries to append a new post to a board. If it can be done, return True
    def new_post(self, board, post):
        if len(self.db[board]) == post.id: # TODO: test for replyTo's value
            self.db[board].append(post)
            return True
        else:
            return False

    # Make a new post with a comment and a replyTo and automaticaly choose the
    # righ ID. Returns the same value as new_post
    def auto_post(self, board, content, replyTo):
        id = self.next_id(board)
        post = Post(id = id, content = content, replyTo = replyTo)
        return self.new_post(board, post)

    # Reads the db to find the last few posts
    def get_last_posts(self, board, num):
        if num > len(self.db[board]):
            num = len(self.db[board])
        reply = []
        for i in range(len(self.db[board])-1, len(self.db[board])-num-1, -1):
            reply.append(self.db[board][i])
        return reply

    # Returns a specific post by its ID
    # Also returns a boolean telling if the search was successfull
    def get_post(self, board, id):
        try:
            if self.db[board][id].id == id: # Everything is well
                return self.db[board][id], True
            else:
                raise IndexError # Force a pass in the except block
        except IndexError:
            return None, False

    # Return the fisrt few post replying to an other post
    def get_first_replies(self, board, num, id):
        ret = []
        for i in self.db[board][id+1:-1]:
            if i.replyTo == id:
                ret.append(i)
                if len(ret) == num:
                    break
        return ret

# ---------------------------------- Testing --------------------------------- #

if __name__ == '__main__':
    db = DataBase()
    print('\n -- Testing posting -- \n')
    for i in range(10):
        db.auto_post('t', str(i), 0)
    print(db)
    print('\n -- Testing reading some posts -- \n')
    print(db.get_last_posts('t', 4))
    print(db.get_last_posts('t', 0))
    print(db.get_last_posts('t', 1))
    print(db.get_last_posts('t', 11))
    print(db.get_last_posts('t', 12))
    print('\n -- Testing reading post by ID -- \n')
    print(db.get_post('t', 4))
    print(db.get_post('t', -1))
    print(db.get_post('t', 100))
    print('\n -- Testing reading thread -- \n')
    print(db.get_first_replies('t', 4, 0))

