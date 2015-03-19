import sqlite3

from passlib.hash import bcrypt

FIND_USER_QUERY = 'SELECT (name, password, response_body) FROM users WHERE '\
        'name = ?'

class SqliteBackend(object):
    def __init__(self, config):
        self._connection = sqlite3.connect(config.database or 'data/sins.sqlite3')

    def try_login(self, username, password):
        users = [u for u in self._connection.execute(FIND_USER_QUERY, username)]
        if not users:
            return None

        user = users[0]
        if not bcrypt.verify(password, user['password']):
            return None
        del user['password']

        return user

def create(config):
    return SqliteBackend(config)
