'''
Helpful nice to haves for FAR.

'''

import uuid

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
