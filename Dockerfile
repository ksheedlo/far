FROM python:2.7

MAINTAINER Ken Sheedlo <ovrkenthousand@gmail.com>

ENV FAR_CONFIG /srv/far/config/config.json
ENV PYTHONUNBUFFERED true

RUN apt-get update \
  && apt-get -y install \
    xmlsec1 \
  && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN mkdir -p /srv/far
COPY . /srv/far/

VOLUME /srv/far/keys
VOLUME /srv/far/config
WORKDIR /srv/far/src/far

EXPOSE 5000
CMD ["gunicorn", \
  "-b", "0.0.0.0:5000", \
  "-k", "eventlet", \
  "--limit-request-line=8190", \
  "-R", \
  "-w", "1", \
  "far:app"]
