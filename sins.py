#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import backends.identity
import base64
import json
import os
import urllib
import sys

from backends.errors import IdentityError
from datetime import datetime, timedelta
from flask import (Flask, abort, redirect, render_template, request,
                    session, url_for)
from xml.etree.ElementTree import ParseError as XMLParseError
from saml2 import class_name, samlp, saml, sigver
from saml2 import VERSION as SAML2_VERSION
from sessions import MemoryStasher
from uuid import uuid1
from validation import SAMLValidator, SAMLValidationError, SAMLSecurityConfig

app = Flask(__name__)

parser = argparse.ArgumentParser(
        description='Stupid SAML Identity Provider app.')
parser.add_argument('--config', '-c', type=str,
        help='The location of the config file.')
args = parser.parse_args()

with open(args.config or 'config.json', 'r') as f:
    config = json.load(f)

backend = backends.identity.create(config)
stasher = MemoryStasher(config)
validator = SAMLValidator(config)

def redirect_to_login(saml_request, relay_state):
    return redirect(url_for('login',
        SAMLRequest=saml_request,
        RelayState=relay_state))

def valid_session():
    return 'user_id' in session and \
        'expires' in session and \
        datetime.today() < session['expires']

def get_name_string(user):
    return "Username={name},DDI={tenant_id},UserID={user_id},Email={email},AuthToken={token}".format(
        name=backend.get_username(user),
        tenant_id=backend.get_tenant_id(user),
        user_id=backend.get_user_id(user),
        email=backend.get_email(user),
        token=backend.get_auth_token(user)
    )

def datetime_to_iso8601(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def clean_assertion_extensions_attributes(attributes):
    # REACH: According to the W3 Spec (http://www.w3.org/TR/xmlschema-1/#xsi_nil),
    # if xsi:nil is set to true, the element must be empty.  This attribute
    # appears after the response is converted to a string for signing
    # and then back into a response object.
    # ksheedlo: what the fuck is this I don't even
    for ndx, _member in enumerate(attributes):
        attributes[ndx].attribute_value[0].extension_attributes.pop(
            '{http://www.w3.org/2001/XMLSchema-instance}nil', None)

    return attributes

def create_saml_response(name_string, request_id, service_url):
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
    name_id = saml.NameID(format=saml.NAMEID_FORMAT_PERSISTENT, text=name_string)
    not_on_or_after = datetime.today() + timedelta(minutes=5)
    subject = saml.Subject(name_id=name_id, subject_confirmation=saml.SubjectConfirmation(
        subject_confirmation_data=saml.SubjectConfirmationData(
            not_on_or_after=datetime_to_iso8601(not_on_or_after))))

    # Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn
    authn_statement = saml.AuthnStatement(authn_instant=issue_instant,
        authn_context=saml.AuthnContext(authn_context_class_ref=saml.AuthnContextClassRef(
            text=saml.AUTHN_PASSWORD_PROTECTED)))

    assertion_id = str(uuid1())
    signature_id = 1

    security_context = sigver.security_context(SAMLSecurityConfig(
        cert_file=config['keys']['ssl_cert'], key_file=config['keys']['ssl_key']))
    signature = sigver.pre_signature_part(assertion_id, security_context.my_cert, signature_id)

    response.assertion = saml.Assertion(
        id=assertion_id,
        subject=subject,
        signature=signature,
        authn_statement=authn_statement,
        issuer=saml.Issuer(text=service_url),
        attribute_statement=saml.AttributeStatement(attribute=[]))

    signed_assertion = security_context.sign_assertion(response.assertion.to_string(),
        node_id=assertion_id)
    signed_assertion_response = saml.assertion_from_string(signed_assertion)

    # TO͇̹̺ͅƝ̴ȳ̳ TH̘Ë͖́̉ ͠P̯͍̭O̚​N̐Y̡ H̸̡̪̯ͨ͊̽̅̾̎Ȩ̬̩̾͛ͪ̈́̀́͘ ̶̧̨̱̹̭̯ͧ̾ͬC̷̙̲̝͖ͭ̏ͥͮ͟Oͮ͏̮̪̝͍M̲̖͊̒ͪͩͬ̚̚͜Ȇ̴̟̟͙̞ͩ͌͝
    response.assertion.signature.signature_value = \
        signed_assertion_response.signature.signature_value
    response.assertion.signature.signed_info.reference.digest_value = \
        signed_assertion_response.signature.signed_info.reference[0].digest_value

    response.signature = sigver.pre_signature_part(response.id,
        security_context.my_cert, signature_id)
    response = security_context.sign_statement(response.to_string(), class_name(response))

    final_response = samlp.response_from_string(response)
    final_response.extension_attributes['xmlns:xs'] = 'http://www.w3.org/2001/XMLSchema'
    final_response.assertion[0].attribute_statement[0].attribute = \
        clean_assertion_extensions_attributes(
            final_response.assertion[0].attribute_statement[0].attribute)

    return final_response

def post_sso():
    saml_request = request.form['SAMLRequest']
    relay_state = request.form['RelayState']

    # Check if the user has a session. If the user has a valid session,
    # they are logged in and get the auto-POSTing login form. If they
    # are not logged in, they need to be redirected to the login page.
    if not valid_session():
        return redirect_to_login(saml_request, relay_state)

    user_session = stasher.lookup(session['user_id'])
    if user_session is None:
        return redirect_to_login(saml_request, relay_state)

    return redirect(url_for('try_sso',
        SAMLRequest=saml_request,
        RelayState=relay_state))

def get_sso():
    relay_state = request.args['RelayState']
    saml_response = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'

    try:
        saml_request = validator.validate(request.args['SAMLRequest'])
    except SAMLValidationError as e:
        return abort(400)

    user_session = stasher.lookup(session['user_id'])
    name_string = get_name_string(user_session)

    saml_response = create_saml_response(name_string, saml_request.id,
        saml_request.assertion_consumer_service_url)
    based_response = base64.b64encode(saml_response.to_string())

    return render_template('redirect.html',
        relay_state=relay_state,
        saml_response=based_response)

@app.route('/sso/', methods=['GET', 'POST'])
def try_sso():
    if request.method == 'GET':
        return get_sso()
    return post_sso()

def get_login():
    post_params = {
        'SAMLRequest': request.args['SAMLRequest'],
        'RelayState': request.args['RelayState']
    }

    return render_template('login.html',
        post_params=urllib.urlencode(post_params))

def post_login():
    saml_request = request.args['SAMLRequest']
    relay_state = request.args['RelayState']

    try:
        user = backend.try_login(request.form['username'], request.form['password'])
        user_id = backend.get_user_id(user)
        stasher.stash(user_id, user)
        session['user_id'] = user_id
        session['expires'] = datetime.today() + timedelta(hours=12)
    except IdentityError as e:
        print('An error occurred: {0}'.format(e))

    return redirect(url_for('try_sso',
        SAMLRequest=saml_request,
        RelayState=relay_state))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return get_login()
    return post_login()

def debug_enabled():
    return config.get('debug', {}).get('use_debugger', False)

def reload_enabled():
    return config.get('debug', {}).get('use_reloader', False)

# The secret key is loaded from the config file if available.
# Otherwise, it's created on the fly.
app.secret_key = config.get('secret_key', os.urandom(24))

app.run(use_debugger=debug_enabled(),
    use_reloader=reload_enabled(),
    debug=debug_enabled())
