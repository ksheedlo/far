import base64
import binascii

from saml2 import samlp, sigver

def _find_where(thingies, query):
    for thingie in thingies:
        found = True
        for key in query:
            found = found and key in thingie and thingie[key] == query[key]
        if found:
            return thingie
    return None

class SAMLSecurityConfig(object):
    def __init__(self, cert_file=None, key_file=None):
        self.xmlsec_binary = None
        self.crypto_backend = 'xmlsec1'
        self.only_use_keys_in_metadata = False
        self.metadata = None
        self.generate_cert_info = False
        self.cert_handler_extra_class = None
        self.cert_file = cert_file
        self.key_file = key_file
        self.tmp_cert_file = None
        self.tmp_key_file = None
        self.validate_certificate = False
        self.debug = False

class SAMLValidationError(Exception):
    def __init__(self, message):
        self.message = message

class SAMLValidator(object):
    def __init__(self, config):
        self._service_providers = list(config['service_providers'])

    def validate(self, request_xml):
        # Validation largely cribbed from Reach. Thanks Reach!
        try:
            saml_request_xml = base64.decodestring(request_xml)
        except binascii.Error as e:
            raise SAMLValidationError('SAMLRequest contains an invalid base64 string')

        try:
            saml_request = samlp.authn_request_from_string(saml_request_xml)
        except XMLParseError as e:
            raise SAMLValidationError('SAMLRequest contains invalid XML')

        if not saml_request:
            # samlp.authn_request_from_string returns None if it cannot an request object.
            raise SAMLValidationError('AuthnRequest is malformed')

        service_url = saml_request.assertion_consumer_service_url
        if not service_url:
            raise SAMLValidationError('No AssertionConsumerServiceURL found in AuthnRequest')

        service_provider = self._get_service_provider(saml_request.issuer.text)
        if not service_provider:
            raise SAMLValidationError('Invalid service provider: {0}'.format(saml_request))

        if not saml_request.signature or not saml_request.signature.signature_value:
            raise SAMLValidationError('No SAML request signature found.')

        saml_request_verified = False

        try:
            saml_request_verified = saml_request.verify()
        except Exception as e:
            raise SAMLValidationError('SAML request verification threw an exception.')

        if not saml_request_verified:
            raise SAMLValidationError('SAML request verification failed.')

        security_context = sigver.security_context(SAMLSecurityConfig(
            cert_file=service_provider['public_key']))
        try:
            security_context.correctly_signed_authn_request(saml_request_xml)
        except sigver.SignatureError:
            raise SAMLValidationError('No SSL configuration worked for ' +
                'service provider: {sp} with saml request: {xml}'.format(
                sp=service_provider['id'], xml=saml_request_xml))

        return saml_request

    def _get_service_provider(self, issuer):
        return _find_where(self._service_providers, { 'issuer': issuer })
