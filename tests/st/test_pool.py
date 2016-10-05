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
from test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.exceptions import CommandExecError

"""
Test calicoctl pool

1) Test the CRUD aspects of the pool commands.
2) Test IP assignment from pool.

BGP exported routes are hard to test and aren't expected to change much so
write tests for them (yet)

"""

ipv4_yaml = """
- apiVersion: v1
  kind: pool
  metadata:
    cidr: 10.0.1.0/24
  spec:
    ipip:
      enabled: true
"""

ipv6_yaml = """
- apiVersion: v1
  kind: pool
  metadata:
    cidr: fed0:8001::/64
  spec:
"""


class TestPool(TestBase):
    def test_pool_crud(self):
        """
        Test that a basic CRUD flow for pool commands.
        """
        with DockerHost('host', dind=False, start_calico=False) as host:
            # Set up the ipv4 and ipv6 pools to use
            ipv4_pool = "10.0.1.0/24"
            ipv6_pool = "fed0:8001::/64"

            # Run pool commands to add the ipv4 pool and show the pools
            host.calicoctl("pool add %s" % ipv4_pool)
            pool_out = host.calicoctl("pool show")

            # Assert output contains the ipv4 pool, but not the ipv6
            self.assertIn(ipv4_pool, pool_out)
            self.assertNotIn(ipv6_pool, pool_out)

            # Run pool commands to add the ipv6 pool and show the pools
            host.calicoctl("pool add %s" % ipv6_pool)
            pool_out = host.calicoctl("pool show")

            # Assert output contains both the ipv4 pool and the ipv6
            self.assertIn(ipv4_pool, pool_out)
            self.assertIn(ipv6_pool, pool_out)

            # Remove both the ipv4 pool and ipv6 pool
            host.calicoctl("pool remove %s" % ipv4_pool)
            host.calicoctl("pool remove %s" % ipv6_pool)
            pool_out = host.calicoctl("pool show")

            # Assert the pool show output does not contain either pool
            self.assertNotIn(ipv4_pool, pool_out)
            self.assertNotIn(ipv6_pool, pool_out)

            # Assert that deleting the pool again fails.
            self.assertRaises(CommandExecError,
                              host.calicoctl, "pool remove %s" % ipv4_pool)

            # Write out some yaml files to load in through calicoctl-go
            # We could have sent these via stdout into calicoctl, but this
            # seemed easier.
            with open('ipv4.yaml', 'w') as f:
                f.write(ipv4_yaml)
            with open('ipv6.yaml', 'w') as f:
                f.write(ipv6_yaml)
            # Create the ipv4 network using the Go calicoctl
            host.calicoctl("create -f ipv6.yaml", new=True)
            # And read it back out using the python calicoctl
            pool_out = host.calicoctl("pool show")
            # Assert output contains the ipv6 pool, but not the ipv4
            self.assertNotIn(ipv4_pool, pool_out)
            self.assertIn(ipv6_pool, pool_out)
            self.assertNotIn("ipip", pool_out)

            # Now read it out with the Go calicoctl too:
            pool_out = host.calicoctl("get pool", new=True)
            # Assert output contains the ipv4 pool, but not the ipv6
            self.assertNotIn(ipv4_pool, pool_out)
            self.assertIn(ipv6_pool, pool_out)
            self.assertNotIn("ipip", pool_out)

            # Add in the ipv6 network with Go calicoctl
            host.calicoctl("create -f ipv4.yaml", new=True)
            # And read it back out using the python calicoctl
            pool_out = host.calicoctl("pool show")
            # Assert output contains both the ipv4 pool and the ipv6
            self.assertIn(ipv4_pool, pool_out)
            self.assertIn(ipv6_pool, pool_out)
            self.assertIn("ipip", pool_out)

            # Now read it out with the Go calicoctl too:
            pool_out = host.calicoctl("get pool", new=True)
            # Assert output contains both the ipv4 pool and the ipv6
            self.assertIn(ipv4_pool, pool_out)
            self.assertIn(ipv6_pool, pool_out)


            # Remove both the ipv4 pool and ipv6 pool
            host.calicoctl("delete -f ipv6.yaml", new=True)
            host.calicoctl("delete -f ipv4.yaml", new=True)
            pool_out = host.calicoctl("pool show")
            # Assert output contains neither network
            self.assertNotIn(ipv4_pool, pool_out)
            self.assertNotIn(ipv6_pool, pool_out)
            self.assertNotIn("ipip", pool_out)
            # Now read it out with the Go calicoctl too:
            pool_out = host.calicoctl("get pool", new=True)
            self.assertNotIn(ipv4_pool, pool_out)
            self.assertNotIn(ipv6_pool, pool_out)
            self.assertNotIn("ipip", pool_out)
