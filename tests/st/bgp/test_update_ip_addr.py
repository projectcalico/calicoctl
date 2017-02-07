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
import json
from nose.plugins.attrib import attr

from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.utils import assert_network, assert_profile, \
    assert_number_endpoints, get_profile_name, ETCD_CA, ETCD_CERT, \
    ETCD_KEY, ETCD_HOSTNAME_SSL, ETCD_SCHEME, get_ip, check_bird_status

from .peer import ADDITIONAL_DOCKER_OPTIONS

class TestUpdateIPAddress(TestBase):

    @attr('slow')
    def test_update_ip_address(self):
        """
        Test updating the IP address automatically updates and fixes the
        Bird BGP config.
        """
        with DockerHost('host1',
                        additional_docker_options=ADDITIONAL_DOCKER_OPTIONS,
                        start_calico=False) as host1, \
             DockerHost('host2',
                        additional_docker_options=ADDITIONAL_DOCKER_OPTIONS,
                        start_calico=False) as host2:

            # Start host1 using the inherited AS, and host2 using a specified
            # AS (same as default).  These hosts use the gobgp backend, whereas
            # host3 uses BIRD.
            host1.start_calico_node("--ip=1.2.3.4")
            host2.start_calico_node("--ip=2.3.4.5")

            # Create a network and a couple of workloads on each host.
            network1 = host1.create_network("subnet1")
            workload_host1 = host1.create_workload("workload1", network=network1)
            workload_host2 = host2.create_workload("workload2", network=network1)

            # Fix the node resources to have the correct IP addresses.
            self._fix_ip(host1)
            self._fix_ip(host2)

            # Allow network to converge
            self.assert_true(workload_host1.check_can_ping(workload_host2.ip, retries=10))

            # Check connectivity in both directions
            self.assert_ip_connectivity(workload_list=[workload_host1,
                                                       workload_host2],
                                        ip_pass_list=[workload_host1.ip,
                                                      workload_host2.ip])

    def _fix_ip(self, host):
        """
        Update the calico node resource to have the correct IP for the host.
        """
        noder = json.loads(host.calicoctl(
            "get node %s --output=json" % host.get_hostname()))
        noder["Spec"]["BGP"]["IPAddress"] = str(host.ip)
        self.writejson("new_data", noder)
        host.calicoctl("apply -f new_data")
