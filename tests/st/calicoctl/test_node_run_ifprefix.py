# Copyright (c) 2015-2016 Tigera, Inc. All rights reserved.
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
from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.exceptions import CommandExecError
from tests.st.utils.utils import retry_until_success
from tests.st.utils.utils import ETCD_CA, ETCD_CERT, \
    ETCD_KEY, ETCD_HOSTNAME_SSL, ETCD_SCHEME, get_ip

"""
Test calicoctl node run --docker-networking-ifprefix=<IFPREFIX>

Most of the status output is checked by the BGP tests, so this module just
contains a simple return code check.
"""

ADDITIONAL_DOCKER_OPTIONS = "--cluster-store=etcd://%s:2379 " % \
                                get_ip()

class TestNodeRunIfprefix(TestBase):
    def test_node_run_ifprefix(self):
        """
        Test that the status command can be executed.
        """
        with DockerHost('host1',
                        additional_docker_options=ADDITIONAL_DOCKER_OPTIONS,
                        start_calico=False) as host1:

            # Start the node on host1 using first-found auto-detection
            # method.
            host1.start_calico_node(
                "--docker-networking-ifprefix=intf")

            host1.create_workload("thingy", "busybox", "bridge", None, [])

            # Attempt to start the node on host2 using can-reach auto-detection
            # method using a bogus DNS name.  This should fail.
            try:
                host1.execute(
                    "ifconfig | grep intf")
            except CommandExecError:
                pass
            else:
                raise AssertionError("Command expected to fail but did not")
