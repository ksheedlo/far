# -*- coding: utf-8 -*-

'''
Session stores for FAR.

All session stores should support the same set of methods,
which is the set of methods that session stores have.
'''

from far.helpers import find_where

class MemoryStore(object):
    '''
    A memory-backed session store.

    '''
    def __init__(self):
        self._data = []

    def create_session(self, session_id, data):
        '''
        Creates a new session.

        '''
        self._data.append({
            'data': data,
            'service_providers': [],
            'session_id': session_id})

    def lookup_by_session_id(self, session_id):
        '''
        Gets the session for the specified session ID.

        '''
        entry = find_where(self._data, {'session_id': session_id})
        return None if entry is None else entry['data']

    def add_service_provider_session(self, session_id, service_provider_id):
        '''
        Activates a service provider for the session.

        '''
        entry = find_where(self._data, {'session_id': session_id})

        if entry:
            entry['service_providers'].append(service_provider_id)

    def remove_service_provider_session(self, session_id, service_provider_id):
        '''
        Removes a service provider from the session.

        '''
        entry = find_where(self._data, {'session_id': session_id})

        if entry:
            entry['service_providers'] = [
                sp for sp in entry['service_providers']
                if sp != service_provider_id]

    def logged_in_service_providers(self, session_id):
        '''
        A list of active service providers for the specified session.

        '''
        entry = find_where(self._data, {'session_id': session_id})

        if entry:
            return entry['service_providers']
        return []

    def destroy_session(self, session_id):
        '''
        Destroys a session.

        '''
        self._data = [d for d in self._data if d['session_id'] != session_id]

# pylint: disable=unused-argument
def create_store_from_config(config):
    '''
    Given a configuration object, create the correct session store.

    '''
    # ಠ_ಠ: Support choosing other stores besides memory.
    # These will be configured using the session_store.store
    # and session_store.options config options.
    return MemoryStore()
# pylint: enable=unused-argument
