import requests

class IdentityBackend(object):
    def __init__(self, config):
        self._identity_endpoint = config['identity_endpoint'] or
            'https://identity.api.rackspacecloud.com/v2.0/tokens'

    def try_login(self, username, password):
        pass

def create(config):
    return IdentityBackend(config)
