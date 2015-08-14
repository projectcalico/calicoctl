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

from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.workload import NET_NONE
from tests.st.utils.defaults import (IPV4_POOL_ADDR_1, IPV4_POOL_ADDR_2,
                                     IPV6_POOL_ADDR_1, IPV6_POOL_ADDR_2,
                                     DEFAULT_IPV4_POOL, DEFAULT_IPV6_POOL)


class TestNoOrchestratorSingleHost(TestBase):
    def test_single_host(self):
        """
        Test mainline functionality without using an orchestrator plugin
        """
        with DockerHost('host', dind=False, ipv6=True) as host:
            host.calicoctl("profile add TEST_GROUP")

            # Use standard docker bridge networking for one and --net=none
            # for the other.  Do this for both IPv4 and IPv6.
            node1 = host.create_workload("node1")
            node2 = host.create_workload("node2", network=NET_NONE)

            # Repeat for IPv6
            node3 = host.create_workload("node3", image="ubuntu", ipv6=True)
            node4 = host.create_workload("node4", image="ubuntu", ipv6=True,
                                         network=NET_NONE)

            # TODO - find a better home for this assertion
            # # Attempt to configure the nodes with the same profiles.  This will
            # # fail since we didn't use the driver to create the nodes.
            # with self.assertRaises(CalledProcessError):
            #     host.calicoctl("profile TEST_GROUP member add %s" % node1)
            # with self.assertRaises(CalledProcessError):
            #     host.calicoctl("profile TEST_GROUP member add %s" % node2)

            # Add the nodes to Calico networking.
            host.calicoctl("container add %s %s" % (node1, IPV4_POOL_ADDR_1))
            host.calicoctl("container add %s %s" % (node2, IPV4_POOL_ADDR_2))

            # Repeat for IPv6 nodes
            host.calicoctl("container add %s %s" % (node3, IPV6_POOL_ADDR_1))
            host.calicoctl("container add %s %s" % (node4, IPV6_POOL_ADDR_2))

            # Get the endpoint IDs for the containers
            ep1 = host.calicoctl("container %s endpoint-id show" % node1)
            ep2 = host.calicoctl("container %s endpoint-id show" % node2)

            # Repeat for IPv6 nodes
            ep3 = host.calicoctl("container %s endpoint-id show" % node3)
            ep4 = host.calicoctl("container %s endpoint-id show" % node4)

            # Now add the profiles - one using set and one using append
            host.calicoctl("endpoint %s profile set TEST_GROUP" % ep1)
            host.calicoctl("endpoint %s profile append TEST_GROUP" % ep2)

            # Repeat for IPv6
            host.calicoctl("endpoint %s profile set TEST_GROUP" % ep3)
            host.calicoctl("endpoint %s profile append TEST_GROUP" % ep4)

            # TODO - assert on output of endpoint show and endpoint profile
            # show commands.

            # Check it works
            node1.assert_can_ping(IPV4_POOL_ADDR_2, retries=3)
            node2.assert_can_ping(IPV4_POOL_ADDR_1, retries=3)
            node3.assert_can_ping(IPV6_POOL_ADDR_2, retries=3)
            node4.assert_can_ping(IPV6_POOL_ADDR_1, retries=3)

            # Test the teardown commands
            host.calicoctl("profile remove TEST_GROUP")
            host.calicoctl("container remove %s" % node1)
            host.calicoctl("container remove %s" % node2)
            host.calicoctl("container remove %s" % node3)
            host.calicoctl("container remove %s" % node4)
            host.calicoctl("pool remove %s" % DEFAULT_IPV4_POOL)
            host.calicoctl("pool remove %s" % DEFAULT_IPV6_POOL)
            host.calicoctl("node stop")
