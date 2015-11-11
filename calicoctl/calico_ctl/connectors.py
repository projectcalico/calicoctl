# Copyright 2015 Metaswitch Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import docker
import docker.errors

from pycalico.ipam import IPAMClient
from pycalico.datastore import (ETCD_AUTHORITY_ENV, ETCD_AUTHORITY_DEFAULT,
                                ETCD_SCHEME_ENV, ETCD_SCHEME_DEFAULT, 
                                ETCD_KEY_FILE_ENV, ETCD_CERT_FILE_ENV,
                                ETCD_CA_CERT_FILE_ENV, DataStoreError)
from utils import DOCKER_VERSION
from utils import print_paragraph
from utils import validate_hostname_port

# If an ETCD_AUTHORITY is specified in the environment variables, validate
# it.
etcd_authority = os.getenv(ETCD_AUTHORITY_ENV, ETCD_AUTHORITY_DEFAULT)
if etcd_authority and not validate_hostname_port(etcd_authority):
    print_paragraph("Invalid %s. It must take the form <address>:<port>. "
                    "Value provided is '%s'" % (ETCD_AUTHORITY_ENV,
                                                etcd_authority))
    sys.exit(1)

# Check etcd environment values for etcd with SSL/TLS
etcd_scheme = os.getenv(ETCD_SCHEME_ENV, ETCD_SCHEME_DEFAULT)
etcd_key_file = os.getenv(ETCD_KEY_FILE_ENV, "")
etcd_cert_file = os.getenv(ETCD_CERT_FILE_ENV, "")
etcd_ca_cert_file = os.getenv(ETCD_CA_CERT_FILE_ENV, "")

#TODO: Remove these prints after getting it working
print "etcd_scheme is %s" % etcd_scheme
print "etcd_key is %s" % etcd_key_file
print "etcd_cert is %s" % etcd_cert_file
print "etcd_ca is %s" % etcd_ca_cert_file

try:
    #TODO: Remove print after working
    print "Creating IPAM client"
    client = IPAMClient()
except DataStoreError as e:
    print_paragraph(e.message)
    sys.exit(1)

_base_url=os.getenv("DOCKER_HOST", "unix://var/run/docker.sock")
docker_client = docker.Client(version=DOCKER_VERSION, base_url=_base_url)
