import json
import requests

from errors import IdentityError

class IdentityBackend(object):
    def __init__(self, config):
        self._identity_endpoint = config.get('backend', {}
            ).get('identity_endpoint') or \
            'http://localhost:8900/identity'

    def try_login(self, username, password):
        payload = json.dumps({
            'auth': {
                'passwordCredentials': {
                    'username': username,
                    'password': password
                }
            }
        })
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json'
        }
        r = requests.post('{0}/v2.0/tokens'.format(self._identity_endpoint),
            data=payload, headers=headers)
        r.raise_for_status()
        result = r.json()
        if 'unauthorized' in result:
            raise IdentityError('Login attempt failed')
        return result

    def get_user_id(self, user):
        return user['access']['user']['id']

    def get_tenant_id(self, user):
        return user['access']['token']['tenant']['id']

    def get_username(self, user):
        return user['access']['user']['name']

    def get_auth_token(self, user):
        return user['access']['token']['id']

    def get_email(self, user):
        """
        Gets the email for the account.

        Returns the email address as a string, or None if there is no email
        address on the account OR if the identity backend does not support
        the required API to fetch it.
        """
        username = self.get_username(user)
        headers = {
            'user-agent': 'Rackspace SINS SSO Double;{0}'.format(username),
            'x-auth-token': self.get_auth_token(user)
        }
        r = requests.get('{0}/v2.0/users'.format(self._identity_endpoint),
            params={'name': username}, headers=headers)

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Alternative identity backends (such as Mimic) might not support
            # this API. Mimic will return a 404, so we handle the 404 here
            # and re-raise all other errors.
            if e.message.startswith('404'):
                return None
            raise e

        result = r.json()
        if 'unauthorized' in result:
            raise IdentityError('Unauthorized attempt to get the email address')
        return result['user'].get('email')

def create(config):
    return IdentityBackend(config)
