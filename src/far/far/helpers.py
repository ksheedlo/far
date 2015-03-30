'''
Helpful nice to haves for FAR.

'''

import urllib
import urlparse
import uuid

from far.errors import BadMongoAuthCredentials

def find_where(thingies, query):
    '''
    A python implementation of Underscore's _.findWhere().

    '''
    for thingie in thingies:
        found = True
        for key in query:
            found = found and key in thingie and thingie[key] == query[key]
        if found:
            return thingie
    return None

def datetime_to_iso8601(dat):
    '''
    Converts a Python datetime to the ISO 8601 format used by SAML.

    '''
    return dat.strftime('%Y-%m-%dT%H:%M:%SZ')

def generate_far_id():
    '''
    Generates a unique identifier for a thing.

    '''
    return 'FAR-{0}'.format(uuid.uuid1())

def generate_signature_id():
    '''
    Generates a different kind of unique identifier.

    '''
    return int(uuid.uuid1())

def _encode_uri_component(sss):
    '''
    Does proper Unicode-aware URL quoting.

    '''
    return urllib.quote(sss.encode('utf-8'))

# pylint: disable=too-many-arguments
def mongodb_connect_url(hostname, database, port=27017, username=None, password=None):
    '''
    Gets the URL for connecting to MongoDB.

    '''
    auth = ''
    if username is not None:
        if password is None:
            raise BadMongoAuthCredentials('Must specify a password when specifying username!')
        auth = _encode_uri_component(username) + ':' + _encode_uri_component(password) + '@'
    elif password is not None:
        raise BadMongoAuthCredentials('Must specify a username when specifying password!')

    host = hostname
    if port:
        host = host + ':' + str(port)

    return urlparse.urlunsplit(['mongodb',
                                auth + host,
                                '/' + database,
                                '', ''])
# pylint: enable=too-many-arguments
