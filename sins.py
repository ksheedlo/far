#!/usr/bin/env python

from __future__ import print_function

import argparse
import backends.identity
import json
import os
import urllib
import sys

from backends.errors import IdentityError
from datetime import datetime, timedelta
from flask import Flask, redirect, render_template, request, session, url_for
from sessions import MemoryStasher

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

def redirect_to_login(saml_request, relay_state):
    return redirect(url_for('login',
        SAMLRequest=saml_request,
        RelayState=relay_state))

def valid_session():
    return 'user_id' in session and \
        'expires' in session and \
        datetime.today() < session['expires']

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

    return render_template('redirect.html',
        relay_state=relay_state,
        saml_response=saml_response)

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
