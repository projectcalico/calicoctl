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
import copy
import netaddr
import logging
import netaddr
import yaml
from nose_parameterized import parameterized

from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.exceptions import CommandExecError
from tests.st.utils.utils import assert_network, assert_profile, \
    assert_number_endpoints, get_profile_name, ETCD_CA, ETCD_CERT, \
    ETCD_KEY, ETCD_HOSTNAME_SSL, ETCD_SCHEME, get_ip

POST_DOCKER_COMMANDS = ["docker load -i /code/calico-node.tar",
                        "docker load -i /code/busybox.tar",
                        "docker load -i /code/workload.tar"]

if ETCD_SCHEME == "https":
    ADDITIONAL_DOCKER_OPTIONS = "--cluster-store=etcd://%s:2379 " \
                                "--cluster-store-opt kv.cacertfile=%s " \
                                "--cluster-store-opt kv.certfile=%s " \
                                "--cluster-store-opt kv.keyfile=%s " % \
                                (ETCD_HOSTNAME_SSL, ETCD_CA, ETCD_CERT,
                                 ETCD_KEY)
else:
    ADDITIONAL_DOCKER_OPTIONS = "--cluster-store=etcd://%s:2379 " % \
                                get_ip()

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)


class MultiHostIpam(TestBase):
    @classmethod
    def setUpClass(cls):
        super(TestBase, cls).setUpClass()
        cls.hosts = []
        cls.hosts.append(DockerHost("host1",
                                    additional_docker_options=ADDITIONAL_DOCKER_OPTIONS,
                                    post_docker_commands=POST_DOCKER_COMMANDS,
                                    start_calico=False))
        cls.hosts.append(DockerHost("host2",
                                    additional_docker_options=ADDITIONAL_DOCKER_OPTIONS,
                                    post_docker_commands=POST_DOCKER_COMMANDS,
                                    start_calico=False))
        cls.hosts[0].start_calico_node()
        cls.hosts[1].start_calico_node()
        cls.network = cls.create_network(cls.hosts[0], "testnet1")
        cls.workloads = []

    @classmethod
    def tearDownClass(cls):
        # Tidy up
        for host in cls.hosts:
            host.remove_workloads()
        cls.network.delete()
        for host in cls.hosts:
            host.cleanup()
            del host

    def test_pools_add(self):
        """
        Add a pool, create containers, check IPs assigned from pool.
        Then Delete that pool.
        Add a new pool, create containers, check IPs assigned from NEW pool
        """
        response = self.hosts[0].calicoctl("get IPpool -o yaml")
        pools = yaml.safe_load(response)
        self.hosts[0].writefile("pools.yaml", response)

        ipv4_subnet = None
        for pool in pools:
            network = netaddr.IPNetwork(pool['metadata']['cidr'])
            if network.version == 4:
                ipv4_subnet = netaddr.IPNetwork(pool['metadata']['cidr'])
        assert ipv4_subnet is not None

        for host in self.hosts:
            workload = host.create_workload("wld-%s" % host.name,
                                            image="workload",
                                            network=self.network)
            assert netaddr.IPAddress(workload.ip) in ipv4_subnet

        self.hosts[0].calicoctl("delete -f pools.yaml")

        ipv4_subnet = netaddr.IPNetwork("10.0.1.0/24")
        new_pool = {'apiVersion': 'v1',
                    'kind': 'ipPool',
                    'metadata': {'cidr': str(ipv4_subnet.ipv4())},
                    }
        self.hosts[0].writefile("pools.yaml", yaml.dump(new_pool))
        self.hosts[0].calicoctl("create -f pools.yaml")

        for host in self.hosts:
            workload = host.create_workload("wld2-%s" % host.name,
                                            image="workload",
                                            network=self.network)
            assert netaddr.IPAddress(workload.ip) in ipv4_subnet, \
                "Workload IP in wrong pool. IP: %s, Pool: %s" % (workload.ip, ipv4_subnet.ipv4())

    @parameterized.expand([
        # Can't use boolean values here :(
        "False",
        "True",
    ])
    def test_pool_wrap(self, make_static_workload_str):
        """
        Repeatedly create and delete workloads until the system re-assigns an IP.
        """
        # Convert make_static_workload_str into a bool
        make_static_workload = False
        if make_static_workload_str == "True":
            make_static_workload = True
        # Get details of the current pool.
        response = self.hosts[0].calicoctl("get IPpool -o yaml")
        pools = yaml.safe_load(response)
        ipv4_subnet = None
        for pool in pools:
            network = netaddr.IPNetwork(pool['metadata']['cidr'])
            if network.version == 4:
                ipv4_subnet = netaddr.IPNetwork(pool['metadata']['cidr'])
        assert ipv4_subnet is not None

        host = self.hosts[0]
        i = 0
        if make_static_workload:
            static_workload = host.create_workload("static",
                                                   image="workload",
                                                   network=self.network)
            i += 1

        new_workload = host.create_workload("wld-%s" % i,
                                            image="workload",
                                            network=self.network)
        assert netaddr.IPAddress(new_workload.ip) in ipv4_subnet
        original_ip = new_workload.ip
        while True:
            host.execute("docker rm -f %s" % new_workload.name)
            i += 1
            new_workload = host.create_workload("wld-%s" % i,
                                                image="workload",
                                                network=self.network)
            assert netaddr.IPAddress(new_workload.ip) in ipv4_subnet
            if make_static_workload:
                assert new_workload.ip != static_workload.ip, "IPAM assigned an IP which is " \
                                                              "still in use!"

            if new_workload.ip == original_ip:
                # We assign pools to hosts in /26's - so 64 addresses.
                poolsize = 64
                # But if we're using one for a static workload, there will be one less
                if make_static_workload:
                    poolsize -= 1
                assert i >= poolsize, "Original IP was re-assigned before entire host pool " \
                                "was cycled through.  Hit after %s times" % i
                break
            if i > (len(ipv4_subnet) * 2):
                assert False, "Cycled twice through pool - original IP still not assigned."

        # Clear up static workload
        if make_static_workload:
            host.execute("docker rm -f %s" % static_workload.name)

    @staticmethod
    def create_network(host, net_name):
        """
        Creates a docker network, deleting any that existed with that name first.
        :param host: The host (DockerHost object) to run the docker commands on
        :param net_name: string.  The name of the network to create.
        :return: the DockerNetwork object created.
        """
        # Check if network is present before we create it
        try:
            host.execute("docker network inspect %s" % net_name)
            # Network exists - delete it
            host.execute("docker network rm " + net_name)
        except CommandExecError:
            # Network didn't exist, no problem.
            pass
        return host.create_network(net_name, ipam_driver="calico-ipam")
