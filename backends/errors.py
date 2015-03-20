class Http400(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)
