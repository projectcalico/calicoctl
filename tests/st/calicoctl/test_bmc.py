# Copyright (c) 2015-2017 Tigera, Inc. All rights reserved.
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
import json
import logging
import copy

from nose_parameterized import parameterized

from tests.st.test_base import TestBase
from tests.st.utils.utils import log_and_run, calicoctl, \
    API_VERSION, name, ERROR_CONFLICT, NOT_FOUND, NOT_NAMESPACED, \
    SET_DEFAULT, NOT_SUPPORTED
from tests.st.utils.data import *

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)


class TestCalicoctlCommands(TestBase):
    """
    Test calicoctl pool
    1) Test the CRUD aspects of the pool commands.
    2) Test IP assignment from pool.
    BGP exported routes are hard to test and aren't expected to change much so
    write tests for them (yet)
    """


    @parameterized.expand([
        (networkpolicy_name1_rev1,),
        (workloadendpoint_name1_rev1,),
    ])
    def test_namespaced(self, data):
        """
        Tests namespace is handled as expected for each namespaced resource type.
        """
        # Clone the data so that we can modify the metadata parms.
        data1 = copy.deepcopy(data)
        data2 = copy.deepcopy(data)

        kind = data['kind']

        # Create resource with name1 and with name2.
        # Leave the first namespace blank and the second set to
        # namespace2 for the actual create request.
        if kind == "WorkloadEndpoint":
            # The validation in libcalico-go WorkloadEndpoint checks the
            # construction of the name so keep the name on the workloadendpoint.

            # Below namespace2 is searched for the WorkloadEndpoint data1
            # name so we need data2 to have a different name than data1 so we
            # change it to have eth1 instead of eth0

            # Strip off the last character (the zero in eth0) and replace it
            # with a 1
            data2['metadata']['name'] = data1['metadata']['name'][:len(data1['metadata']['name'])-1] + "1"
            # Change endpoint to eth1 so the validation works on the WEP
            data2['spec']['endpoint'] = "eth1"
        else:
            data1['metadata']['name'] = "name1"
            data2['metadata']['name'] = "name2"

        data1['metadata']['namespace'] = ""
        data2['metadata']['namespace'] = "namespace2"

        rc = calicoctl("create", data=data1)
        rc.assert_no_error()
        rc = calicoctl("create", data=data2)
        rc.assert_no_error()

        # We expect the namespace to be defaulted to "default"
        # if not specified.  Tweak the namespace in data1 to be default so that
        # we can use it to compare against the calicoctl get output.
        data1['metadata']['namespace'] = "default"

        if kind == "WorkloadEndpoint":
            data1['metadata']['labels']['projectcalico.org/namespace'] = 'default'

        # Get the resource with name1 and namespace2.  For a namespaced
        # resource this should match the modified data to default the
        # namespace.
        rc = calicoctl("get %s %s --namespace default -o yaml" % (kind, data1['metadata']['name']))
        data1['metadata']['uid'] = rc.decoded['metadata']['uid']
        rc.assert_data(data1)

        if kind == "WorkloadEndpoint":
            data2['metadata']['labels']['projectcalico.org/namespace'] = 'namespace2'

        # Get the resource type for all namespaces.  For a namespaced resource
        # this will return everything.
        rc = calicoctl("get %s --all-namespaces -o yaml" % kind)
        #data2['metadata']['uid'] = rc.decoded['metadata']['uid']
        rc.assert_list(kind, [data1, data2])

        # For namespaced resources, if you do a list without specifying the
        # namespace we'll just get the default namespace.
        rc = calicoctl("get %s -o yaml" % kind)
        rc.assert_list(kind, [data1])

        # For namespaced resources, if you do a list specifying a namespace
        # we'll get results for that namespace.
        rc = calicoctl("get %s -o yaml -n namespace2" % kind)
        rc.assert_list(kind, [data2])

        # Doing a get by file will use the namespace in the file.
        rc = calicoctl("get -o yaml", data1)
        rc.assert_data(data1)
        rc = calicoctl("get -o yaml", data2)
        rc.assert_data(data2)

        # Doing a get by file will use the default namespace if not specified
        # in the file or through the CLI args.
        data1_no_ns = copy.deepcopy(data1)
        del (data1_no_ns['metadata']['namespace'])
        rc = calicoctl("get -o yaml", data1_no_ns)
        rc.assert_data(data1)
        rc = calicoctl("get -o yaml -n namespace2", data1_no_ns)
        rc.assert_error(NOT_FOUND)

        data2_no_ns = copy.deepcopy(data2)
        del(data2_no_ns['metadata']['namespace'])
        rc = calicoctl("get -o yaml -n namespace2", data2_no_ns)
        rc.assert_data(data2)
        rc = calicoctl("get -o yaml", data2_no_ns)
        rc.assert_error(NOT_FOUND)

        # Deleting without a namespace will delete the default.
        rc = calicoctl("delete %s %s" % (kind, data1['metadata']['name']))
        rc.assert_no_error()

        rc = calicoctl("delete %s %s" % (kind, data2['metadata']['name']))
        rc.assert_error(NOT_FOUND)
        rc = calicoctl("delete", data2)
        rc.assert_no_error()

