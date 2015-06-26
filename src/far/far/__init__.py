# -*- coding: utf-8 -*-

'''
far: Main module

Copyright 2015, Ken Sheedlo
Licensed under MIT.
'''

import base64
import logging
import json
import os
import requests
import sys
import urllib

from datetime import datetime, timedelta
from far.errors import IdentityError, SAMLValidationError
from far.helpers import generate_far_id
from far.identity import IdentityBackend
from far.sessions import (flask_user_create_session, flask_user_session_data,
                          session_interface_and_store_from_config,
                          flask_user_has_valid_session)
from far.sso import SamlSSO
from flask import (Flask, abort, redirect, render_template, request,
                   session, url_for)

# As a Flask app, this module has to declare some variables that pylint
# considers invalid. In particular, the main method of the program is
# effectively here in this section bootstrapping the app. Generally
# setting global variables and having effecting operations in the top
# of a module is bad, but in context we need to suppress the warning.
# pylint: disable=invalid-name
app = Flask('far')

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

config_file = os.environ.get('FAR_CONFIG', 'config.json')
app.logger.debug('Loading config file {0}'.format(config_file))

with open(config_file, 'r') as f:
    far_config = json.load(f)

# The secret key is loaded from the config file if available.
# Otherwise, it's created on the fly.
app.secret_key = far_config.get('secret_key', os.urandom(24))

session_interface, session_store = session_interface_and_store_from_config(
    far_config['session_store'])
if session_interface:
    app.session_interface = session_interface

identity = IdentityBackend(far_config)
sso = SamlSSO(far_config)
# pylint: enable=invalid-name

def _get_name_string(user):
    '''
    Gets the name string to send back to the SP identifying the user.

    '''
    fmt = "Username={name},DDI={tenant_id},UserID={user_id},Email={email},AuthToken={token}"
    return fmt.format(name=identity.get_username(user),
                      tenant_id=identity.get_tenant_id(user),
                      user_id=identity.get_user_id(user),
                      email=identity.get_email(user),
                      token=identity.get_auth_token(user))

def _get_far_url():
    '''
    Gets the configured URL the service is supposed to be at.

    '''
    return far_config['far_url']

def debug_enabled(cfg):
    '''
    Indicates whether debugging mode is enabled in the config.

    '''
    return cfg.get('debug', {}).get('use_debugger', False)

def reload_enabled(cfg):
    '''
    Indicates whether watch and reload is enabled in the config.

    '''
    return cfg.get('debug', {}).get('use_reloader', False)

def redirect_to_login(saml_request, relay_state):
    '''
    Redirects the user to a login screen.

    '''
    return redirect(url_for('login',
                            SAMLRequest=saml_request,
                            RelayState=relay_state))

def valid_session():
    '''
    Indicates whether the user has a currently valid session.

    '''
    return 'user_id' in session and \
        'expires' in session and \
        datetime.today() < session['expires']

def post_sso():
    '''
    Opens the SAML login request workflow.

    POSTing to the SSO endpoint causes the session to be checked and
    the user to be identified. If the user has a session, they are
    redirected to receive the SAML assertion identifying them to the
    service provider. If we don't know who they are, they are redirected
    to log in.
    '''
    saml_request = request.form['SAMLRequest']
    relay_state = request.form['RelayState']

    # Check if the user has a session. If the user has a valid session,
    # they are logged in and get the auto-POSTing login form. If they
    # are not logged in, they need to be redirected to the login page.
    if not flask_user_has_valid_session(session, session_store):
        app.logger.debug('[post_sso] User has no valid session. Redirecting to login.')
        return redirect_to_login(saml_request, relay_state)

    app.logger.debug('[post_sso] User has a valid session. Redirecting to SSO.')
    return redirect(url_for('try_sso',
                            SAMLRequest=saml_request,
                            RelayState=relay_state))

def get_sso():
    '''
    Tries to authenticate the user.

    If successful, this method will render the redirect page with a
    signed SAML LoginResponse containing assertions about their identity.
    '''
    relay_state = request.args['RelayState']

    try:
        saml_request = sso.validate_login_request(request.args['SAMLRequest'])
    except SAMLValidationError:
        app.logger.warning(
            '[get_sso] SAML login request validation failed for session: {0}'.format(
                session['session_id']))
        return abort(400)

    app.logger.debug('[get_sso] SAML login request validation passed.')
    user_session = flask_user_session_data(session, session_store)
    name_string = _get_name_string(user_session)

    saml_response = sso.create_saml_login_response(
        name_string, saml_request.id, session['session_id'],
        saml_request.assertion_consumer_service_url)
    based_response = base64.b64encode(saml_response.to_string())

    return render_template('redirect.html',
                           relay_state=relay_state,
                           saml_response=based_response)

@app.route('/sso/', methods=['GET', 'POST'])
def try_sso():
    '''
    Dispatches both possible methods of the /sso/ route.

    '''
    if request.method == 'GET':
        return get_sso()
    return post_sso()

def get_login():
    '''
    Renders the login page.

    '''
    post_params = {
        'SAMLRequest': request.args['SAMLRequest'],
        'RelayState': request.args['RelayState']
    }

    return render_template('login.html',
                           post_params=urllib.urlencode(post_params))

def post_login():
    '''
    Attempts to log the user in from a form.

    If successful, the user will be redirected to enter the SAML
    LoginResponse workflow.
    '''
    saml_request = request.args['SAMLRequest']
    relay_state = request.args['RelayState']

    try:
        user = identity.try_login(request.form['username'], request.form['password'], app.logger)
        flask_user_create_session(session, session_store, user)
    except IdentityError as ex:
        app.logger.warning('[post_login] Login error: {0}'.format(ex))
        return abort(400)

    app.logger.debug('[post_login] Login successful, redirecting to try SSO.')
    return redirect(url_for('try_sso',
                            SAMLRequest=saml_request,
                            RelayState=relay_state))

@app.route('/', methods=['GET', 'POST'])
def login():
    '''
    Dispatches both possible methods of the / endpoint.

    '''
    if request.method == 'GET':
        return get_login()
    return post_login()

@app.route('/sso/logout/request', methods=['POST'])
def logout_from_service_provider():
    '''
    Logs out the user from their Service Provider.

    A full SAML SSO would also log the user out of any other Service
    Provider sessions they had, but we don't do that yet.
    '''
    logout_request = request.data

    # We really do need to catch all Exceptions here.
    # pylint: disable=broad-except
    try:
        logout_request = sso.validate_logout_request(logout_request)
    except Exception as ex:
        app.logger.warning(('[logout_from_service_provider] SAML logout request ' +
                            'validation failed because of an error: {0}').format(ex))
        return abort(400)

    try:
        session_key = logout_request.session_index[0].text
    except Exception:
        app.logger.warning('[logout_from_service_provider] Logout failed because ' +
                           'it could not get the session key.')
        return abort(400)

    if not session_key:
        app.logger.warning('[logout_from_service_provider] Logout failed because ' +
                           'the session key did not exist.')
        return abort(400)

    logout_response = sso.create_saml_logout_response(
        _get_far_url(), logout_request.id)
    logout_response_xml = logout_response.to_string()
    based_logout_response = base64.b64encode(logout_response_xml)

    issuer = logout_request.issuer.text
    logout_url = sso.get_logout_response_url(issuer)

    try:
        requests.post(logout_url, data=based_logout_response)
    except Exception as ex:
        app.logger.warning(('An error occurred trying to send the logout response ' +
                            'to the Service Provider: {0}\nThe Service Provider was: {1}').format(
                                ex, issuer))
    # pylint: enable=broad-except

    session_store.destroy_session(session_key)
    del session['session_id']

    app.logger.debug(('[logout_from_service_provider] Logout of session {0} ' +
                      'successful. Redirecting to login page.').format(session_key))
    return redirect(url_for('login'))

def main():
    '''
    Runs the app in development mode.
    '''
    app.run(use_debugger=debug_enabled(far_config),
            use_reloader=reload_enabled(far_config),
            debug=debug_enabled(far_config))
