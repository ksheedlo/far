#!/bin/bash

if [[ -n "$1" ]]
then
  NAME="$1"
else
  NAME="sins.rax.io"
fi

openssl req \
    -new \
    -newkey rsa:2048 \
    -days 365 \
    -nodes \
    -x509 \
    -subj "/C=US/ST=California/L=San Francisco/O=Rackspace/OU=Product/CN=sins.rax.io" \
    -keyout "keys/$NAME.key" \
    -out "keys/$NAME.crt"

chmod 400 "keys/$NAME.key"