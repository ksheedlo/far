import uuid

from datetime import datetime
from far.errors import BadMongoAuthCredentials
from far.helpers import (datetime_to_iso8601, find_where, generate_far_id,
                         generate_signature_id, mongodb_connect_url)
from pytest import raises

def test_find_where_finds_the_thingie():
    thingies = [{
        'foo': 'bar'
    }, {
        'foo': 'baz'
    }, {
        'ice': 'zap'
    }]
    assert find_where(thingies, {'foo': 'baz'}) == thingies[1]

def test_find_where_returns_none():
    thingies = [{
        'foo': 'bar'
    }, {
        'foo': 'ice'
    }, {
        'foo': 'quuuuuuuuux'
    }]
    assert find_where(thingies, {'foo': 'baz'}) is None

def test_generate_signature_id(monkeypatch):
    monkeypatch.setattr(uuid, 'uuid1', lambda: '309952557696108969718832816538440004746')
    assert generate_signature_id() == 309952557696108969718832816538440004746L

def test_generate_far_id(monkeypatch):
    monkeypatch.setattr(uuid, 'uuid1', lambda: '1f2ecf2e-d5e7-11e4-893e-3c15c2e1748a')
    assert generate_far_id() == 'FAR-1f2ecf2e-d5e7-11e4-893e-3c15c2e1748a'

def test_datetime_to_iso8601():
    assert datetime_to_iso8601(datetime(2015, 3, 29, 0, 47, 34, 215383)) == '2015-03-29T00:47:34Z'

def test_mongodb_connect_url():
    assert mongodb_connect_url('example.com', 'data') == \
        'mongodb://example.com:27017/data'

def test_mongodb_connect_url_with_params():
    assert mongodb_connect_url(
        'mongo.cat.photography', 'catpix', username='grumpycat', password='meowmix',
        port=12345) == \
            'mongodb://grumpycat:meowmix@mongo.cat.photography:12345/catpix'

def test_mongodb_connect_no_auto_reconnect():
    assert mongodb_connect_url('example.com', 'data') == \
        'mongodb://example.com:27017/data'

def test_mongodb_missing_password_raises():
    with raises(BadMongoAuthCredentials):
        mongodb_connect_url('example.com', 'data', username='bob')

def test_mongodb_missing_username_raises():
    with raises(BadMongoAuthCredentials):
        mongodb_connect_url('example.com', 'data', password='letmein')
