#!/usr/bin/env python

import argparse
import json
import os
import sys

from flask import Flask, request

app = Flask(__name__)

parser = argparse.ArgumentParser(
        description='Stupid SAML Identity Provider app.')
parser.add_argument('--config', '-c', type=str,
        help='The location of the config file.')
args = parser.parse_args()

with open(args.config or 'config.json', 'r') as f:
    config = json.load(f)

@app.route('/sso/', methods=['POST'])
def start_sso():
    saml_request = request.form['SAMLRequest']
    relay_state = request.form['RelayState']

    return redirect(url_for('login',
        SAMLRequest=saml_request,
        RelayState=relay_state,
        next='/sso/'))

@app.route('/', methods=['GET'])
def login():
    pass

@app.route('/login', methods=['GET', 'POST'])
def root():
    if request.method == 'GET':
        return app.send_static_file('login.html')
    return 'Got a POST'

# The secret key is loaded from the config file if available.
# Otherwise, it's created on the fly.
app.secret_key = config.get('secret_key', os.urandom(24))
app.run()
