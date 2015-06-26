'''
Implements the Identity backend as a Keystone client.

'''

import json
import requests

from far.errors import IdentityError

# pylint: disable=no-self-use
class IdentityBackend(object):
    '''
    Identity backend class.

    '''
    def __init__(self, config):
        self._identity_endpoint = config.get('backend', {}
                                            ).get('identity_endpoint') or \
                                            'http://localhost:8900/identity'

    def try_login(self, username, password, logger):
        '''
        Tries to log in to Keystone with the provided credentials.

        It also works for any Keystone-compatible API implementing
        username and password authentication, e.g., Mimic.
        '''
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
        logger.debug('-> POST {0}/v2.0/tokens'.format(self._identity_endpoint))
        req = requests.post('{0}/v2.0/tokens'.format(self._identity_endpoint),
                            data=payload, headers=headers)
        req.raise_for_status()
        result = req.json()
        if 'unauthorized' in result:
            raise IdentityError('Login attempt failed')
        return result

    def get_user_id(self, user):
        '''
        Gets the user ID from the user data blob.

        '''
        return user['access']['user']['id']

    def get_tenant_id(self, user):
        '''
        Gets the tenant ID from the user data blob.

        '''
        return user['access']['token']['tenant']['id']

    def get_username(self, user):
        '''
        Gets the username from the user data blob.

        '''
        return user['access']['user']['name']

    def get_auth_token(self, user):
        '''
        Gets the auth token from the user data blob.

        '''
        return user['access']['token']['id']

    def get_email(self, user):
        '''
        Gets the email for the account.

        Returns the email address as a string, or None if there is no email
        address on the account OR if the identity backend does not support
        the required API to fetch it.
        '''
        username = self.get_username(user)
        headers = {
            'user-agent': 'Rackspace FAR SSO Double;{0}'.format(username),
            'x-auth-token': self.get_auth_token(user)
        }
        req = requests.get('{0}/v2.0/users'.format(self._identity_endpoint),
                           params={'name': username}, headers=headers)

        try:
            req.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            # Alternative identity backends (such as Mimic) might not support
            # this API. Mimic will return a 404, so we handle the 404 here
            # and re-raise all other errors.
            if str(ex.message).startswith('404'):
                return None
            raise ex

        result = req.json()
        if 'unauthorized' in result:
            raise IdentityError('Unauthorized attempt to get the email address')
        return result['user'].get('email')
# pylint: enable=no-self-use
