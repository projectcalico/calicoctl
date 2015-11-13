#!/bin/sh
set -e
set -x

# Ensure the main and testing repros are present. Needed for runit
echo "http://alpine.gliderlabs.com/alpine/edge/testing" >> /etc/apk/repositories

# These packages make it into the final image.
apk -U add runit python py-setuptools libffi ip6tables ipset iputils iproute2

# These packages are only used for building and get removed.
apk add --virtual temp python-dev libffi-dev py-pip alpine-sdk curl cmake

# Install Confd
curl -L https://github.com/projectcalico/confd/releases/download/v0.10.0-scale/confd.static -o /sbin/confd
curl -L https://github.com/lloyd/yajl/archive/2.1.0.tar.gz -o /tmp/2.1.0.tar.gz
tar zxf /tmp/2.1.0.tar.gz
cd ./yajl-2.1.0 && ./configure && make install && cd .. && rm -r ./yajl-2.1.0

# Copy patched BIRD daemon with tunnel support.
curl -L https://github.com/projectcalico/calico-bird/releases/download/v0.1.0/bird -o /sbin/bird
curl -L https://github.com/projectcalico/calico-bird/releases/download/v0.1.0/bird6 -o /sbin/bird6
curl -L https://github.com/projectcalico/calico-bird/releases/download/v0.1.0/birdcl -o /sbin/birdcl
chmod +x /sbin/*

# Install Felix
pip install git+https://github.com/projectcalico/calico.git

# Output the python library list
pip list > libraries.txt

# Cleanup
apk del temp && rm -rf /var/cache/apk/*
