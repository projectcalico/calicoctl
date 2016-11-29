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
import random
import unittest
import yaml
from nose_parameterized import parameterized
from multiprocessing.dummy import Pool

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
        (Add a pool), create containers, check IPs assigned from pool.
        Then Delete that pool.
        Add a new pool, create containers, check IPs assigned from NEW pool
        """
        unittest.skip("remove me")
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
            workload = host.create_workload("wlda-%s" % host.name,
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
            workload = host.create_workload("wlda2-%s" % host.name,
                                            image="workload",
                                            network=self.network)
            assert netaddr.IPAddress(workload.ip) in ipv4_subnet, \
                "Workload IP in wrong pool. IP: %s, Pool: %s" % (workload.ip, ipv4_subnet.ipv4())

    def test_ipam_show(self):
        """
        Create some workloads, then ask calicoctl to tell you about the IPs in the pool.
        Check that the correct IPs are shown as in use.
        """
        num_workloads = 10
        workloads = []
        workload_ips = []

        # Get existing pools and write to file to restore later
        response = self.hosts[0].calicoctl("get IPpool -o yaml")
        self.hosts[0].writefile("pools.yaml", response)
        # Delete any existing pools
        self.hosts[0].calicoctl("delete -f pools.yaml")

        ipv4_subnet = netaddr.IPNetwork("192.168.45.0/25")
        new_pool = {'apiVersion': 'v1',
                    'kind': 'ipPool',
                    'metadata': {'cidr': str(ipv4_subnet.ipv4())},
                    }
        self.hosts[0].writefile("newpool.yaml", yaml.dump(new_pool))
        self.hosts[0].calicoctl("create -f newpool.yaml")

        for i in range(num_workloads):
            host = random.choice(self.hosts)
            workload = host.create_workload("wlds-%s" % i,
                                            image="workload",
                                            network=self.network)
            workloads.append((workload, host))
            workload_ips.append(workload.ip)

        print workload_ips

        for ip in ipv4_subnet:
            response = self.hosts[0].calicoctl("ipam show --ip=%s" % ip)
            if "No attributes defined for" in response:
                # This means the IP is assigned
                assert str(ip) in workload_ips, "ipam show says IP %s is assigned when it is not" % ip
            if "not currently assigned in block" in response:
                # This means the IP is not assigned
                assert str(ip) not in workload_ips, \
                    "ipam show says IP %s is not assigned when it is!" % ip

        pool = Pool(3)
        result = pool.map(self.delete_workload, workloads)
        pool.close()
        pool.join()

        # Tidy up workloads
        for workload, host in workloads:
            self.delete_workload(host, workload)
        # Delete new pool
        self.hosts[0].calicoctl("delete -f newpool.yaml")
        # Restore IP pools
        self.hosts[0].calicoctl("create -f pools.yaml")

    @parameterized.expand([
        # Can't use boolean values here :(
        "False",
        "True",
    ])
    def test_pool_wrap(self, make_static_workload_str):
        """
        Repeatedly create and delete workloads until the system re-assigns an IP.
        """
        unittest.skip("remove me")
        # Convert make_static_workload_str into a bool
        make_static_workload = False
        if make_static_workload_str == "True":
            make_static_workload = True

        # Get existing pools and write to file to restore later
        response = self.hosts[0].calicoctl("get IPpool -o yaml")
        self.hosts[0].writefile("pools.yaml", response)
        # Delete any existing pools
        self.hosts[0].calicoctl("delete -f pools.yaml")

        ipv4_subnet = netaddr.IPNetwork("192.168.46.0/25")
        new_pool = {'apiVersion': 'v1',
                    'kind': 'ipPool',
                    'metadata': {'cidr': str(ipv4_subnet.ipv4())},
                    }
        self.hosts[0].writefile("newpool.yaml", yaml.dump(new_pool))
        self.hosts[0].calicoctl("create -f newpool.yaml")

        host = self.hosts[0]
        i = 0
        if make_static_workload:
            static_workload = host.create_workload("static",
                                                   image="workload",
                                                   network=self.network)
            i += 1

        new_workload = host.create_workload("wldw-%s" % i,
                                            image="workload",
                                            network=self.network)
        assert netaddr.IPAddress(new_workload.ip) in ipv4_subnet
        original_ip = new_workload.ip
        while True:
            self.delete_workload(host, new_workload)
            i += 1
            new_workload = host.create_workload("wldw-%s" % i,
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
        # Clear out any lingering workloads
        self.delete_workload(host, new_workload)

        # Clear up static workload
        if make_static_workload:
            self.delete_workload(host, static_workload)

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

    @staticmethod
    def delete_workload(host, workload):
        host.calicoctl("ipam release --ip=%s" % workload.ip)
        host.execute("docker rm -f %s" % workload.name)
