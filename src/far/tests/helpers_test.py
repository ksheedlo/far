from far.helpers import find_where

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
