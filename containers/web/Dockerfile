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
  far

WORKDIR /srv/far

RUN pip install -r requirements.txt

USER far
WORKDIR /srv/far/src/far
