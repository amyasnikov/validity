FROM python:3.12-slim

ARG NETBOX_VERSION=develop

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git postgresql-client libpq-dev gcc  build-essential \
    && pip install --upgrade pip

# Install NetBox
RUN mkdir -p /opt/netbox \
    && git clone --single-branch --branch=${NETBOX_VERSION} https://github.com/netbox-community/netbox.git /opt/netbox/ \
    && pip install -r /opt/netbox/requirements.txt

# Install Validity
COPY . /plugin/validity
COPY ./development/start.sh /opt/netbox/netbox/
RUN pip install --editable /plugin/validity[dev]

WORKDIR /opt/netbox/netbox/
