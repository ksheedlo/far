# -*- coding: utf-8 -*-

'''
Session stores for FAR.

All session stores should support the same set of methods,
which is the set of methods that session stores have.
'''

import pymongo

from datetime import datetime, timedelta
from far.helpers import find_where, mongodb_connect_url, generate_far_id
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

def _new_expiration():
    '''
    Returns a new expiration datetime object.

    Expiration is defined as 12 hours in the future.
    '''
    return datetime.utcnow() + timedelta(hours=12)

class MemorySsoStore(object):
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
            'expires': _new_expiration(),
            'service_providers': [],
            'session_id': session_id})

    def _backend_get_by_session_id(self, session_id):
        '''
        Gets the session with the requested session ID.

        If the session is expired, it is ignored and the function returns
        None. If there is no session with the requested ID, None is also
        returned.
        '''
        entry = find_where(self._data, {'session_id': session_id})

        if not entry:
            return None

        if entry['expires'] <= datetime.utcnow():
            return None

        return entry

    def lookup_by_session_id(self, session_id):
        '''
        Gets the session for the specified session ID.

        '''
        entry = self._backend_get_by_session_id(session_id)
        return None if entry is None else entry['data']

    def add_service_provider_session(self, session_id, service_provider_id):
        '''
        Activates a service provider for the session.

        '''
        entry = self._backend_get_by_session_id(session_id)

        if entry:
            entry['service_providers'].append(service_provider_id)

    def remove_service_provider_session(self, session_id, service_provider_id):
        '''
        Removes a service provider from the session.

        '''
        entry = self._backend_get_by_session_id(session_id)

        if entry:
            entry['service_providers'] = [
                sp for sp in entry['service_providers']
                if sp != service_provider_id]

    def logged_in_service_providers(self, session_id):
        '''
        A list of active service providers for the specified session.

        '''
        entry = self._backend_get_by_session_id(session_id)

        if entry:
            return entry['service_providers']
        return []

    def destroy_session(self, session_id):
        '''
        Destroys a session.

        '''
        now = datetime.utcnow()
        self._data = [
            d for d in self._data
            if d['session_id'] != session_id and d['expires'] > now]

class MongoSsoStore(object):
    '''
    A MongoDB-backed session store.

    '''
    def __init__(self, database):
        self._sessions = database.sso_sessions

    def create_session(self, session_id, data):
        '''
        Creates a new session.

        '''
        self._sessions.insert({'_id': session_id,
                               'data': data,
                               'expires': _new_expiration(),
                               'service_providers': []})

    def _get_backend_session_by_id(self, session_id):
        '''
        Gets the Mongo session object.

        Might be undefined, so check the result of this function.
        '''
        sess = self._sessions.find_one({'_id': session_id})

        if not sess:
            return None

        if sess['expires'] <= datetime.utcnow():
            return None

        return sess

    def lookup_by_session_id(self, session_id):
        '''
        Gets the session for the specified session ID.

        '''
        sess = self._get_backend_session_by_id(session_id)

        if sess:
            return sess['data']
        return None

    def add_service_provider_session(self, session_id, service_provider_id):
        '''
        Activates a service provider for the session.

        '''
        sess = self._get_backend_session_by_id(session_id)

        if not sess:
            return

        service_providers = list(sess['service_providers'])
        service_providers.append(service_provider_id)
        self._sessions.update({'_id': session_id},
                              {'service_providers': service_providers})

    def remove_service_provider_session(self, session_id, service_provider_id):
        '''
        Removes a service provider from the session.

        '''
        sess = self._get_backend_session_by_id(session_id)

        if not sess:
            return

        service_providers = [
            sp for sp in sess['service_providers'] if sp != service_provider_id]
        self._sessions.update({'_id': session_id},
                              {'service_providers': service_providers})

    def logged_in_service_providers(self, session_id):
        '''
        A list of active service providers for the specified session.

        '''
        sess = self._get_backend_session_by_id(session_id)

        if not sess:
            return None

        return sess['service_providers']

    def destroy_session(self, session_id):
        '''
        Destroys a session.

        '''
        self._sessions.remove({'_id': session_id})

class MongoSession(CallbackDict, SessionMixin):
    '''
    Mongo-backed session class.

    '''
    def __init__(self, initial=None, sid=None):
        CallbackDict.__init__(self, initial)
        self.sid = sid
        self.modified = False

# This interface has more methods than we chose to implement,
# and pylint doesn't know it has reasonable default methods.
# pylint: disable=interface-not-implemented
class MongoSessionInterface(SessionInterface):
    '''
    MongoDB session backend.

    '''
    def __init__(self, database):
        self._sessions = database.sessions

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if sid:
            stored_session = self._sessions.find_one({'_id': sid})
            if stored_session:
                if stored_session.get('expires') > datetime.utcnow():
                    return MongoSession(initial=stored_session['data'],
                                        sid=stored_session['_id'])
        sid = generate_far_id()
        return MongoSession(sid=sid)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            response.delete_cookie(app.session_cookie_name, domain=domain)
            return
        expires = self.get_expiration_time(app, session)
        if not expires:
            expires = datetime.utcnow() + timedelta(hours=12)
        self._sessions.update({'_id': session.sid},
                              {'_id': session.sid,
                               'data': session,
                               'expires': expires}, True)
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=self.get_expiration_time(app, session),
                            httponly=True, domain=domain)
# pylint: enable=interface-not-implemented

def _configured_mongodb_database(config):
    '''
    Gets a handle to a MongoDB database according to configuration.

    '''
    dbname = config['db']
    connect_url = mongodb_connect_url(config['hostname'], dbname,
                                      port=config.get('port', 27017),
                                      username=config.get('username'),
                                      password=config.get('password'))
    client = pymongo.MongoClient(connect_url)
    return client[dbname]

# pylint: disable=invalid-name
def session_interface_and_store_from_config(config):
    '''
    Gets the session interface, if any, and session store respectively.

    If the resulting session interface is not None, it should be set on
    the Flask app. Otherwise, the default session interface should be used.
    '''
    if config['store'] == 'mongodb':
        database = _configured_mongodb_database(config['options'])
        interface = MongoSessionInterface(database)
        store = MongoSsoStore(database)
        return interface, store
    return None, MemorySsoStore()
# pylint: enable=invalid-name

def flask_user_create_session(flask_session, store, data):
    '''
    Given a Flask session, create the session against the specified store.

    '''
    session_id = generate_far_id()
    flask_session['session_id'] = session_id
    store.create_session(session_id, data)

def flask_user_session_data(flask_session, store):
    '''
    Given a Flask session, look up the corresponding SSO session.

    '''
    session_id = flask_session.get('session_id')
    if not session_id:
        return None
    return store.lookup_by_session_id(session_id)

def flask_user_has_valid_session(flask_session, store):
    '''
    Indicates whether the Flask session corresponds to a valid SSO session.

    '''
    sess = flask_user_session_data(flask_session, store)
    return sess is not None

def flask_system_session_data(session_id, store):
    '''
    Given an SSO session id, get the SSO session.

    '''
    return store.lookup_by_session_id(session_id)
