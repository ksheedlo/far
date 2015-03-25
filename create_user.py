#!/usr/bin/env python

from __future__ import print_function

import argparse
import getpass
import json
import sqlite3
import sys

from passlib.hash import bcrypt

PROGRAM_DESCRIPTION = 'Add a user to the SQLite database used by the FAR' \
    ' SQLite plugin.'

INSERT_QUERY = 'INSERT INTO users (name, password, response_body) ' \
        'VALUES (?, ?, ?)'

def get_username():
    unix_user = getpass.getuser()
    name = raw_input('Username [{0}]: '.format(unix_user))
    return name or unix_user

def get_password():
    _prompt = lambda: (getpass.getpass(), getpass.getpass('Retype password: '))
    p1, p2 = _prompt()

    while p1 != p2:
        print('Passwords do not match. Try again')
        p1, p2 = _prompt()

    return p1

def add_user(conn, name, password, template_contents):
    c = conn.cursor()
    c.execute(INSERT_QUERY, (name, password, template_contents))
    conn.commit()

def main(args):
    parser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION)
    parser.add_argument('--template', '-t', type=str,
            help='The location of the user info template response.')
    parser.add_argument('--name', '-n', type=str, help='The username.')
    parser.add_argument('--config', '-c', type=str, help='The location of the'\
            ' config file.')
    args = parser.parse_args()

    with open(args.config or 'config.json', 'r') as f:
        config = json.load(f)

    template = args.template or 'templates/user_info.xml'
    with open(template, 'r') as f:
        template_contents = f.read()

    name = args.name or get_username()
    password = get_password()

    hashed_password = bcrypt.encrypt(password)
    conn = sqlite3.connect(config.get('database', 'data/far.sqlite3'))
    add_user(conn, name, hashed_password, template_contents)
    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
