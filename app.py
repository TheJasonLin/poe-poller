"""This module polls the GGG API and stores the results in Redis."""

import os
import re
import time

import redis
import requests

REDIS_HOST = os.environ['REDIS_HOST']
REDIS = redis.Redis(host=REDIS_HOST, port=6379)

API_URL = 'http://www.pathofexile.com/api/public-stash-tabs'
URL_ID_PARAM = 'id'
REDIS_CHANGE_ID = 'next_change_id'
REDIS_RING_KEY = 'rings'



def get_next_update() -> str:
    """ Get Next Update from GGG's API
    Returns:
        Next Change ID
    """
    params = {}
    if REDIS.exists(REDIS_CHANGE_ID):
        params[URL_ID_PARAM] = REDIS.get(REDIS_CHANGE_ID)

    response = requests.get(API_URL, params=params)

    if response.status_code != 200:
        return None

    body = response.json()
    next_change_id = body['next_change_id']

    REDIS.set(REDIS_CHANGE_ID, next_change_id)

    rings = []

    for stash in body['stashes']:
        stash_name = stash['stash']

        for item in stash['items']:
            league = item['league']
            if not is_desired_league(league):
                break
            if not is_ring(item):
                break
            item['stashName'] = stash_name
            rings.append(item)

    if len(rings) > 0:
        REDIS.rpush(REDIS_RING_KEY, *rings)

    return next_change_id

def is_desired_league(league) -> bool:
    """ . """
    return league == 'Harbinger'

def contains(needle, haystack) -> bool:
    """ source: https://stackoverflow.com/questions/5319922/python-check-if-word-is-in-a-string """
    return re.compile(r'\b({0})\b'.format(needle)).search(haystack) != None

def is_ring(item) -> bool:
    """ . """
    base = item['typeLine']
    if not contains('Ring', base):
        return False
    return True

if __name__ == "__main__":
    while True:
        NEXT_ID = get_next_update()
        if NEXT_ID is not None:
            print(NEXT_ID)
        time.sleep(2)
        