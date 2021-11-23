#!/usr/bin/env python3
"""
This file contains the code used to prevent spamming. It prevents a single user to
post to often. It is IP-based.
"""

from flask import request
import time
import json

# Dictionary of all time to wait indexed by IP
all_users_time = {}

# --------------------------------- Constants -------------------------------- #

# Default time to wait between two posts
TIME_TO_WAIT_MILLIS = 5000

# Each time a user makes a new post, its time to wait until it can post again is multiplied
TIME_TO_WAIT_MULTIPLICATOR = 1.8

# Fortunately, after a time, the multiplier is reset
MULTIPLIER_TIMEOUT_MS = 100_000

# ----------------------------- Helper functions ----------------------------- #

def millis():
    "Returns the current time in UNIX milliseconds."
    return int(time.time_ns() / 1_000_000)

def init_timeout():
    "When a user has no entry in the wait DB, generates a new entry."
    ret = {
            "last_post": millis(),
            "multiplier": 1,
            }
    return ret

def time_until_next_post(timeout):
    """Return the time in milliseconds until the user with
    the given timeout will be allowed to post."""
    time_to_wait = int(timeout["multiplier"] * TIME_TO_WAIT_MILLIS)
    end = timeout["last_post"] + time_to_wait
    now = millis()
    return end - now

def is_allowed_to_post(timeout):
    next_post = time_until_next_post(timeout)
    return next_post < 0

def is_free_from_timeout(timeout):
    "Tells if we should remove a user from the list of timeouts."
    end = timeout["last_post"] + MULTIPLIER_TIMEOUT_MS * timeout["multiplier"]
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
            to_del.append(k)
    for k in to_del:
        all_users_time.pop(k)

def search_in_sorted(array, elem):
    "Find if the given element is in the sorted array. TODO"
    try:
        array.index(elem)
        return True
    except ValueError:
        return False

# --------------------------------- Main API --------------------------------- #

def manage_request(request):
    try:
        timeout = all_users_time[get_IP(request)]
        if is_allowed_to_post(timeout):
            if is_free_from_timeout(timeout):
                gc_list()
            update_user(timeout)
            return True, 0
        else:
            update_user(timeout)
            next_post = time_until_next_post(timeout)
            return False, next_post
    except KeyError:
        all_users_time[get_IP(request)] = init_timeout()
        return True, 0

def get_IP(request):
    "Returns the IP of the sender, even being an Nginx reverse-proxy."
    return hash(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))

# ------------------------------ Handeling bans ------------------------------ #

# Reads a JSON of banned IP hashed
BANNED_IP_FILE = "bans.json"
try:
    with open(BANNED_IP_FILE, "r") as f:
        file_content = f.read()
    list_of_bans = json.loads(file_content)
    for banned in list_of_bans:
        all_users_time[banned] = init_timeout()
        # Ban people simply have an infinitely long time to wait before posting again.
        all_users_time[banned]["multiplier"] = 10**10 
except:
    print("Error, unable to open list of banned IPs.")


# ---------------------------------- Testing --------------------------------- #

def sleep_millis(millis):
    time.sleep(millis / 1000)

if __name__ == '__main__':
    MULTIPLIER_TIMEOUT_MS = 10_000
    def get_IP(x):
        return x
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

