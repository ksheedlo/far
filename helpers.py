import unittest

def find_where(thingies, query):
    for thingie in thingies:
        found = True
        for key in query:
            found = found and key in thingie and thingie[key] == query[key]
        if found:
            return thingie
    return None

class TestHelpers(unittest.TestCase):
    def test_find_where_finds_the_thingie(self):
        thingies = [{
            'foo': 'bar'
        }, {
            'foo': 'baz'
        }, {
            'ice': 'zap'
        }]
        self.assertEqual(find_where(thingies, {'foo': 'baz'}), thingies[1])

    def test_find_where_returns_none(self):
        thingies = [{
            'foo': 'bar'
        }, {
            'foo': 'ice'
        }, {
            'foo': 'quuuuuuuuux'
        }]
        self.assertIsNone(find_where(thingies, {'foo': 'baz'}))

if __name__ == "__main__":
    unittest.main()