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
