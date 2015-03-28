import json
import sqlite3

from helpers import find_where

INSERT_SESSION_QUERY = 'INSERT INTO sessions (user_id, session) VALUES (?, ?)'

class MemoryStasher(object):
    def __init__(self, config):
        self._data = []

    def stash(self, session_id, data):
        self._data.append({
            'data': data,
            'service_providers': [],
            'session_id': session_id })

    def lookup_by_session_id(self, session_id):
        entry = find_where(self._data, { 'session_id': session_id })
        return None if entry is None else entry['data']

    def add_service_provider_session(self, session_id, service_provider_id):
        entry = find_where(self._data, { 'session_id': session_id })

        if entry:
            entry['service_providers'].append(service_provider_id)

    def remove_service_provider_session(self, session_id, service_provider_id):
        entry = find_where(self._data, { 'session_id': session_id })

        if entry:
            entry['service_providers'] = [
                sp for sp in entry['service_providers']
                if sp != service_provider_id ]

    def logged_in_service_providers(self, session_id):
        entry = find_where(self._data, { 'session_id': session_id })

        if entry:
            return entry['service_providers']
        return []

    def drop(self, session_id):
        self._data = [d for d in self._data if d['session_id'] != session_id]

class SessionStasher(object):
    def __init__(self, config):
        self._connection = sqlite3.connect(config.database or 'data/far.sqlite3')

    def stash(self, user_id, data):
        c = self._connection.cursor()
        c.execute(INSERT_SESSION_QUERY, user_id, json.dumps(data))
        self._connection.commit()

    def lookup_by_user_id(self, user_id):
        pass
