#!/bin/bash

apt-get update && \
    apt-get install -qy curl python-dev python-pip git libffi-dev libssl-dev
pip install -r requirements.txt