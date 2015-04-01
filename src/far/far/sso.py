# -*- coding: utf-8 -*-

'''
SAML SSO is fancy. Fancy code is here.

Do you understand it? /\\/\\╭(ಠಠ_ ಠಠ)╮/\\/\\
'''

import base64
import binascii

from datetime import datetime, timedelta
from far.errors import SAMLValidationError
from far.helpers import (datetime_to_iso8601, generate_far_id, generate_signature_id,
                         find_where)
from saml2 import create_class_from_xml_string, class_name, samlp, saml, sigver
from saml2 import VERSION as SAML2_VERSION
from uuid import uuid1
from xml.etree.ElementTree import ParseError as XMLParseError

# pylint: disable=interface-not-implemented
# pylint: disable=too-many-instance-attributes,too-few-public-methods
class SAMLSecurityConfig(object):
    '''
    Some kind of config object that gets sent down into SAML.

    '''
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
# pylint: enable=too-many-instance-attributes,too-few-public-methods

def clean_assertion_exts_attributes(attributes):
    '''
    What is this? I don't even.

    REACH: According to the W3 Spec (http://www.w3.org/TR/xmlschema-1/#xsi_nil),
    if xsi:nil is set to true, the element must be empty.  This attribute
    appears after the response is converted to a string for signing
    and then back into a response object.
    '''
    for ndx, _ in enumerate(attributes):
        attributes[ndx].attribute_value[0].extension_attributes.pop(
            '{http://www.w3.org/2001/XMLSchema-instance}nil', None)

    return attributes

class SamlSSO(object):
    '''
    A big ugly ball of SSO code. Most of it is configured, so it's a class.

    '''
    def __init__(self, config):
        self._config = config

    def _get_service_provider(self, issuer):
        '''
        Gets the Service Provider configuration for the specified issuer.

        '''
        return find_where(self._config['service_providers'], {'issuer': issuer})

    def _security_context_for_signing(self):
        '''
        Gets a Security Context that can be used to sign assertions.

        '''
        return sigver.security_context(
            SAMLSecurityConfig(cert_file=self._config['keys']['ssl_cert'],
                               key_file=self._config['keys']['ssl_key']))

    def validate_login_request(self, request_xml):
        '''
        Validates a LoginRequest.

        Validation largely cribbed from Reach. Thanks Reach!
        '''
        try:
            saml_request_xml = base64.decodestring(request_xml)
        except binascii.Error:
            raise SAMLValidationError('SAMLRequest contains an invalid base64 string')

        try:
            saml_request = samlp.authn_request_from_string(saml_request_xml)
        except XMLParseError:
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
        except Exception:
            raise SAMLValidationError('SAML request verification threw an exception.')

        if not saml_request_verified:
            raise SAMLValidationError('SAML request verification failed.')

        security_context = sigver.security_context(SAMLSecurityConfig(
            cert_file=service_provider['public_key']))
        try:
            security_context.correctly_signed_authn_request(saml_request_xml)
        except sigver.SignatureError:
            raise SAMLValidationError(
                ('No SSL configuration worked for service provider: {sp} with' +
                 ' saml request: {xml}').format(sp=service_provider['id'],
                                                xml=saml_request_xml))

        return saml_request

    def validate_logout_request(self, request_xml):
        '''
        Validates a LogoutRequest.

        '''
        try:
            saml_request_xml = base64.decodestring(request_xml)
        except binascii.Error:
            raise SAMLValidationError('SAMLRequest contains an invalid base64 string')

        try:
            saml_request = samlp.logout_request_from_string(saml_request_xml)
        except XMLParseError:
            raise SAMLValidationError('SAMLRequest contains invalid XML')

        if not saml_request:
            raise SAMLValidationError('SAML LogoutRequest is malformed')

        issuer = saml_request.issuer.text
        if not issuer:
            raise SAMLValidationError('SAML LogoutRequest contains no issuer')

        service_provider = self._get_service_provider(issuer)
        if not service_provider:
            raise SAMLValidationError('Invalid issuer: {0}'.format(issuer))

        if not saml_request.signature or not saml_request.signature.signature_value:
            raise SAMLValidationError('No SAML LogoutRequest signature found')

        saml_request_verified = False

        try:
            saml_request_verified = saml_request.verify()
        except Exception:
            raise SAMLValidationError('SAML LogoutRequest verification threw an exception.')

        if not saml_request_verified:
            raise SAMLValidationError('SAML LogoutRequest verification failed.')

        security_context = sigver.security_context(SAMLSecurityConfig(
            cert_file=service_provider['public_key']))
        try:
            security_context.crypto.validate_signature(
                saml_request_xml, security_context.cert_file, 'pem',
                'LogoutRequest', saml_request.id, 'ID')
        except sigver.SignatureError:
            raise SAMLValidationError(
                ('No SSL configuration worked for service provider: {sp} with' +
                 ' saml request: {xml}').format(sp=service_provider['id'],
                                                xml=saml_request_xml))

        return saml_request

    def _sign_saml_document(self, document):
        '''
        Signs a SAML document.

        '''
        document_type = type(document)
        signature_id = generate_signature_id()

        security_context = self._security_context_for_signing()
        document.signature = sigver.pre_signature_part(
            document.id, security_context.my_cert, signature_id)
        document = security_context.sign_statement(document.to_string(), class_name(document))
        return create_class_from_xml_string(document_type, document)

    def create_saml_logout_request(self, issuer_url, session_id, username):
        '''
        Creates a new SAML LogoutRequest.

        '''
        issue_instant = datetime.utcnow()

        request = samlp.LogoutRequest()
        request.id = generate_far_id()
        request.version = SAML2_VERSION
        request.issue_instant = datetime_to_iso8601(issue_instant)
        request.issuer = saml.Issuer(text=issuer_url)
        request.name_id_policy = samlp.NameIDPolicy(format=saml.NAMEID_FORMAT_PERSISTENT,
                                                    allow_create="true")
        request.session_index = samlp.SessionIndex(session_id)
        request.name_id = saml.NameID(format=saml.NAMEID_FORMAT_PERSISTENT, text=username)
        request.not_on_or_after = datetime_to_iso8601(issue_instant + timedelta(minutes=2))
        return self._sign_saml_document(request)

    def create_saml_logout_response(self, issuer_url, in_response_to):
        '''
        Creates a new SAML LogoutResponse.

        '''
        issue_instant = datetime.utcnow()

        response = samlp.LogoutResponse()
        response.id = generate_far_id()
        response.version = SAML2_VERSION
        response.issue_instant = datetime_to_iso8601(issue_instant)
        response.issuer = saml.Issuer(text=issuer_url)
        response.in_response_to = in_response_to
        response.status = samlp.Status(status_code=samlp.StatusCode(value=samlp.STATUS_SUCCESS))
        return self._sign_saml_document(response)

    def create_saml_login_response(self, name_string, request_id, session_id, service_url):
        '''
        Creates a new SAML LoginResponse with identity assertions.

        '''
        issue_instant = datetime_to_iso8601(datetime.now())

        response = samlp.Response()
        response.id = 'response_id'
        response.version = SAML2_VERSION
        response.issue_instant = issue_instant
        response.issuer = saml.Issuer(text=service_url)
        response.issuer.attributes = {"xmlns:saml2": "urn:oasis:names:tc:SAML:2.0:assertion"}
        response.in_response_to = request_id
        response.destination = service_url

        response.status = samlp.Status(status_code=samlp.StatusCode(value=samlp.STATUS_SUCCESS))

        # I have no idea what the fuck any of this is or does
        subject = saml.Subject(
            name_id=saml.NameID(format=saml.NAMEID_FORMAT_PERSISTENT, text=name_string),
            subject_confirmation=saml.SubjectConfirmation(
                subject_confirmation_data=saml.SubjectConfirmationData(
                    not_on_or_after=datetime_to_iso8601(
                        datetime.today() + timedelta(minutes=5)))))

        # Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn
        authn_statement = saml.AuthnStatement(
            authn_instant=issue_instant, authn_context=saml.AuthnContext(
                authn_context_class_ref=saml.AuthnContextClassRef(
                    text=saml.AUTHN_PASSWORD_PROTECTED)))
        authn_statement.session_index = session_id

        assertion_id = str(uuid1())
        signature_id = 1

        security_context = self._security_context_for_signing()
        signature = sigver.pre_signature_part(assertion_id, security_context.my_cert, signature_id)

        response.assertion = saml.Assertion(
            id=assertion_id,
            subject=subject,
            signature=signature,
            authn_statement=authn_statement,
            issuer=saml.Issuer(text=service_url),
            attribute_statement=saml.AttributeStatement(attribute=[]))

        signed_assertion_response = saml.assertion_from_string(
            security_context.sign_assertion(response.assertion.to_string(),
                                            node_id=assertion_id))

        # H̸̡̪̯ͨ͊̽̅̾̎Ȩ̬̩̾͛ͪ̈́̀́͘ ̶̧̨̱̹̭̯ͧ̾ͬC̷̙̲̝͖ͭ̏ͥͮ͟Oͮ͏̮̪̝͍M̲̖͊̒ͪͩͬ̚̚͜Ȇ̴̟̟͙̞ͩ͌͝
        response.assertion.signature.signature_value = \
            signed_assertion_response.signature.signature_value
        response.assertion.signature.signed_info.reference.digest_value = \
            signed_assertion_response.signature.signed_info.reference[0].digest_value

        response.signature = sigver.pre_signature_part(
            response.id, security_context.my_cert, signature_id)
        response = security_context.sign_statement(response.to_string(), class_name(response))

        final_response = samlp.response_from_string(response)
        final_response.extension_attributes['xmlns:xs'] = 'http://www.w3.org/2001/XMLSchema'
        final_response.assertion[0].attribute_statement[0].attribute = \
            clean_assertion_exts_attributes(
                final_response.assertion[0].attribute_statement[0].attribute)

        return final_response

    def get_logout_response_url(self, issuer):
        '''
        Gets the url to send LogoutResponses to on the specified issuer.

        '''
        srp = find_where(self._config['service_providers'], {'issuer': issuer})
        if srp:
            return srp['logout_response_endpoint']
        return None
# pylint: disable=interface-not-implemented
