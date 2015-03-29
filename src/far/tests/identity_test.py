import requests

from far.identity import IdentityError
from far.identity import IdentityBackend
from pytest import raises

service_catalog = {
    'access': {
        'token': {
            'RAX-AUTH:authenticatedBy': ['PASSWORD'],
            'expires': '2015-03-30T00:54:06.999-05:00',
            'id': 'token_b36eff72-d907-4df4-a219-929e703cdb01',
            'tenant': {
                'id': '198054996541440',
                'name': '198054996541440'
            }
        },
        'serviceCatalog': [{
            'endpoints': [{
                'region': "ORD",
                'publicURL': 'http://localhost:8900/mimicking/MaasApi-b17a9c/ORD/v1.0/198054996541440',
                'tenantId': '198054996541440'
            }],
            'type': 'rax: monitor',
            'name': 'cloudMonitoring'
        }, {
            'endpoints': [{
                'region': 'ORD',
                'publicURL': 'http://localhost:8900/mimicking/NovaApi-7b710d/ORD/v2/198054996541440',
                'tenantId': '198054996541440'
            }],
            'type': 'compute',
            'name': 'cloudServersOpenStack'
        }],
        'user': {
            'id': '5809126768354327275',
            'roles': [{
                'id': '3',
                'name': 'identity:user-admin',
                'description': 'User Admin Role.'
            }],
            'name': 'DOGE'
        }
    }
}

oops_response = {
    'unauthorized': {
        'message': 'Oops! You dun goofed.'
    }
}

email_response = {
    'user': {
        'email': 'shibe@rackspace.com'
    }
}

class MockResponse(object):
    def __init__(self, data, error=None):
        self._data = data
        self._error = error

    def raise_for_status(self):
        if self._error is not None:
            raise self._error

    def json(self):
        return self._data

def test_it_gets_the_login(monkeypatch):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: MockResponse(service_catalog))
    identity = IdentityBackend({})
    catalog = identity.try_login('DOGE', 'shibe wow')
    assert catalog['access']['user']['id'] == '5809126768354327275'

def test_unauthorized_raises(monkeypatch):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: MockResponse(oops_response))
    identity = IdentityBackend({})
    with raises(IdentityError):
        identity.try_login('DOGE', 'cate trickery')

def test_http_error_propagates(monkeypatch):
    monkeypatch.setattr(
        requests, 'post',
        lambda *args, **kwargs: MockResponse({}, requests.exceptions.HTTPError('404 Derp!')))
    identity = IdentityBackend({})
    with raises(requests.exceptions.HTTPError):
        identity.try_login('cow', 'moooooooooo')

def test_it_gets_the_user_id():
    identity = IdentityBackend({})
    assert identity.get_user_id(service_catalog) == '5809126768354327275'

def test_it_gets_the_tenant_id():
    identity = IdentityBackend({})
    assert identity.get_tenant_id(service_catalog) == '198054996541440'

def test_it_gets_the_username():
    identity = IdentityBackend({})
    assert identity.get_username(service_catalog) == 'DOGE'

def test_it_gets_the_auth_token():
    identity = IdentityBackend({})
    assert identity.get_auth_token(service_catalog) == 'token_b36eff72-d907-4df4-a219-929e703cdb01'

def test_it_gets_the_email(monkeypatch):
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: MockResponse(email_response))
    identity = IdentityBackend({})
    assert identity.get_email(service_catalog) == 'shibe@rackspace.com'

def test_email_is_none_on_404(monkeypatch):
    monkeypatch.setattr(
        requests, 'get',
        lambda *args, **kwargs: MockResponse({}, requests.exceptions.HTTPError('404 Derp!')))
    identity = IdentityBackend({})
    assert identity.get_email(service_catalog) is None

def test_email_otherwise_error_propagates(monkeypatch):
    monkeypatch.setattr(
        requests, 'get',
        lambda *args, **kwargs: MockResponse({}, requests.exceptions.HTTPError('500 Fail')))
    identity = IdentityBackend({})
    with raises(requests.exceptions.HTTPError):
        identity.get_email(service_catalog)
