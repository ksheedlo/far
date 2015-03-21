import json
import sqlite3

INSERT_SESSION_QUERY = 'INSERT INTO sessions (user_id, session) VALUES (?, ?)'

class MemoryStasher(object):
    def __init__(self, config):
        self._data = {}

    def stash(self, user_id, data):
        self._data[user_id] = data

    def lookup(self, user_id):
        return self._data.get(user_id)

class SessionStasher(object):
    def __init__(self, config):
        self._connection = sqlite3.connect(config.database or 'data/sins.sqlite3')

    def stash(self, user_id, data):
        c = self._connection.cursor()
        c.execute(INSERT_SESSION_QUERY, user_id, json.dumps(data))
        self._connection.commit()

    def lookup(self, user_id):
        pass
