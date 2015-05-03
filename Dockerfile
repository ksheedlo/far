FROM debian:jessie

MAINTAINER Ken Sheedlo <ken.sheedlo@rackspace.com>

RUN apt-get update && apt-get install -y \
  libffi-dev \
  libssl-dev \
  python \
  python-dev \
  python-pip

RUN adduser --disabled-login \
  --group \
  --home /srv/far \
  --quiet \
  --system \
  --uid 1000 \
  far

WORKDIR /srv/far

# Users should create the Far key and cert before creating the container.
# This makes configuration easier, since the public key must be made
# available to the Service Provider.
COPY . /srv/far/
RUN chown -R far:far /srv/far/
RUN pip install -r requirements.txt

USER far
WORKDIR /srv/far/src/far
