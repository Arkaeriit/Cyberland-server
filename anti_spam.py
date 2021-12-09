#!/usr/bin/env python3
"""
This file contains the code used to prevent spamming. It prevents a single user to
post to often. It is IP-based.
"""

from flask import request
import time
import json
import hashlib
import base64

# Dictionary of all time to wait indexed by IP
all_users_time = {}

# --------------------------------- Constants -------------------------------- #

# Default time to wait between two posts
TIME_TO_WAIT_MILLIS = 5000

# Each time a user makes a new post, its time to wait until it can post again is multiplied
TIME_TO_WAIT_MULTIPLICATOR = 1.8

# Fortunately, after a time, the multiplier is reset
MULTIPLIER_TIMEOUT_MS = 100_000

# Tells if we set up a wait for first time users
LIMIT_FIRST_CONNECTION = True

# Time to wait between the first connection and the fist post
FIST_CONNECTION_DELAY_MS = 1000 * 60 * 5

# ----------------------------- Helper functions ----------------------------- #

def my_hash(s):
    """A hash-like function that returns a string from a string input.
    It is not strictly a hash because the output have been encoded with
    base64 meaning that its size is not constant."""
    m = hashlib.sha256()
    m.update(s.encode('UTF-8'))
    ret = base64.b64encode(m.digest()[0:15]).decode('ASCII')
    return ret

def millis():
    "Returns the current time in UNIX milliseconds."
    return int(time.time_ns() / 1_000_000)

def init_timeout(limit_first_connection):
    """"When a user has no entry in the wait DB, generates a new entry.
    The boolean argument tells if we should limit the iser if it is their first post."""
    ret = {
            "last_post": millis(),
            "multiplier": 1,
            "extra_delay": 0
            }
    if LIMIT_FIRST_CONNECTION and limit_first_connection:
        ret["extra_delay"] += FIST_CONNECTION_DELAY_MS - TIME_TO_WAIT_MILLIS
        ret["multiplier"] = 1 / TIME_TO_WAIT_MULTIPLICATOR
        ret["first_time"] = True
    else:
        ret["first_time"] = False
    return ret

def time_until_next_post(timeout):
    """Return the time in milliseconds until the user with
    the given timeout will be allowed to post."""
    time_to_wait = int(timeout["multiplier"] * TIME_TO_WAIT_MILLIS) + timeout["extra_delay"]
    end = timeout["last_post"] + time_to_wait
    now = millis()
    return end - now

def is_allowed_to_post(timeout):
    next_post = time_until_next_post(timeout)
    ret = next_post < 0
    if ret:
        timeout["extra_delay"] = 0
    return ret

def is_free_from_timeout(timeout):
    "Tells if we should remove a user from the list of timeouts."
    end = timeout["last_post"] + MULTIPLIER_TIMEOUT_MS * timeout["multiplier"] + timeout["extra_delay"]
    now = millis()
    return now > end

def update_user(timeout):
    "Update the last_post and the multiplier field for an user."
    timeout["multiplier"] = timeout["multiplier"] * TIME_TO_WAIT_MULTIPLICATOR
    timeout["last_post"] = millis()

def gc_list():
    "Compute if any user should be removed from the list of timeouts."
    to_del = []
    for k in all_users_time.keys():
        if is_free_from_timeout(all_users_time[k]):
            all_users_time[k]["multiplier"] = 1
            all_users_time[k]["extra_delay"] = 0

# --------------------------------- Main API --------------------------------- #

manage_request_ret = {
        "OK": 0,
        "Limit": 1,
        "First_time": 2
}

def manage_request(request):
    try:
        timeout = all_users_time[get_IP(request)]
        if is_allowed_to_post(timeout):
            if is_free_from_timeout(timeout):
                gc_list()
            update_user(timeout)
            if LIMIT_FIRST_CONNECTION and timeout["first_time"]:
                verify_user(get_IP(request))
            return manage_request_ret["OK"], 0
        else:
            update_user(timeout)
            next_post = time_until_next_post(timeout)
            return manage_request_ret["Limit"], next_post
    except KeyError:
        all_users_time[get_IP(request)] = init_timeout(True)
        if LIMIT_FIRST_CONNECTION:
            return manage_request_ret["First_time"], FIST_CONNECTION_DELAY_MS
        else:
            return manage_request_ret["OK"], 0

def get_IP(request):
    "Returns the IP of the sender, even being an Nginx reverse-proxy."
    return my_hash(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))

# -------------------------- List of verified users -------------------------- #

VERIFIED_USERS_LIST = "verified.json"
try:
    with open(VERIFIED_USERS_LIST, "r") as f:
        file_content = f.read()
    list_of_verified = json.loads(file_content)
    for user in list_of_verified:
        all_users_time[user] = init_timeout(False)
except:
    print("Error, unable to open list of verified IPs.")

def verify_user(user_id):
    "Add an user to the list of verified users."
    try:
        with open(VERIFIED_USERS_LIST, "r") as f:
            file_content = f.read()
        list_of_verified = json.loads(file_content)
    except:
        list_of_verified = []
    list_of_verified.append(user_id)
    with open(VERIFIED_USERS_LIST, "w") as f:
        f.write(json.dumps(list_of_verified))

# ------------------------------ Handeling bans ------------------------------ #

# Reads a JSON of banned IP hashed
BANNED_IP_FILE = "bans.json"
try:
    with open(BANNED_IP_FILE, "r") as f:
        file_content = f.read()
    list_of_bans = json.loads(file_content)
    for banned in list_of_bans:
        all_users_time[banned] = init_timeout(True)
        # Ban people simply have an infinitely long time to wait before posting again.
        all_users_time[banned]["multiplier"] = 10**10 
except:
    print("Error, unable to open list of banned IPs.")

# ---------------------------------- Filters --------------------------------- #

BAD_WORDS_FILE = "bad_words.json"
bad_words = []
try:
    with open(BAD_WORDS_FILE, "r") as f:
        file_content = f.read()
    bad_words = json.loads(file_content)
except:
    print("Error, unable to open list of banned words.")

def try_to_filter(msg, request):
    """Try to find some of the bad words in the message.
    If they are found, return False and increase the multiplier
    of the IP in the request. If they are not found, return True."""
    m = msg.lower()
    for bad_word in bad_words:
        if m.find(bad_word) != -1:
            timeout = all_users_time[get_IP(request)]
            timeout["multiplier"] *= 100
            return False
    return True
            

# ---------------------------------- Testing --------------------------------- #

def sleep_millis(millis):
    time.sleep(millis / 1000)

if __name__ == '__main__':
    MULTIPLIER_TIMEOUT_MS = 10_000
    def get_IP(x):
        return x
    print("---- Test Filter ----")
    bad_words = ["123"]
    manage_request(3)
    print(try_to_filter("56789", 3))
    print(try_to_filter("5678901234", 3))
    print(all_users_time)
    print("---- Init users ----")
    print(all_users_time)
    print(manage_request(1))
    print(manage_request(2))
    print(all_users_time)
    print("---- Test abusive posts ----")
    print(manage_request(1))
    sleep_millis(3000)
    print(manage_request(2))
    print(all_users_time)
    print("---- Test OK posts ----")
    sleep_millis(6000)
    print(manage_request(1))
    sleep_millis(3000)
    print(manage_request(2))
    print("---- Test GC ----")
    sleep_millis(MULTIPLIER_TIMEOUT_MS * TIME_TO_WAIT_MULTIPLICATOR * TIME_TO_WAIT_MULTIPLICATOR)
    print(manage_request(1))
    print(all_users_time)

