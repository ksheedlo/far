import json
import requests

from errors import IdentityError

class IdentityBackend(object):
    def __init__(self, config):
        self._identity_endpoint = config.get('backend', {}
            ).get('identity_endpoint') or \
            'http://localhost:8900/identity/v2.0/tokens'

    def try_login(self, username, password):
        payload = json.dumps({
            'auth': {
                'passwordCredentials': {
                    'username': username,
                    'password': password
                }
            }
        })
        r = requests.post(self._identity_endpoint,
                data=payload,
                headers={'accept':'application/json'})
        r.raise_for_status()
        result = r.json()
        if 'unauthorized' in result:
            raise IdentityError('Login attempt failed')
        return result

    def get_user_id(self, user):
        return user['access']['token']['tenant']['id']


def create(config):
    return IdentityBackend(config)
