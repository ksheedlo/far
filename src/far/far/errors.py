'''
Exception classes for FAR-specific things.

'''

class IdentityError(Exception):
    '''
    Exception class for errors from the Identity backend.

    '''
    def __init__(self, *args):
        Exception.__init__(self, *args)

class SAMLValidationError(Exception):
    '''
    Exception class for errors in SAML validation as defined by FAR.

    '''
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message
