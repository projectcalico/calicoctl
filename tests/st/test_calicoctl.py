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
import simplejson as json
import yaml
import logging
from netaddr import IPNetwork

from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.exceptions import CommandExecError

from unittest import skip

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)


class TestPool(TestBase):
    """
    Test calicoctl pool

    1) Test the CRUD aspects of the pool commands.
    2) Test IP assignment from pool.

    BGP exported routes are hard to test and aren't expected to change much so
    write tests for them (yet)

    """

    def test_pool_crud(self):
        """
        Test that a basic CRUD flow for pool commands.
        """
        with DockerHost('host', dind=False, start_calico=False) as host:
            # Set up the ipv4 and ipv6 pools to use
            ipv4_net = IPNetwork("10.0.1.0/24")
            ipv6_net = IPNetwork("fed0:8001::/64")

            ipv4_pool_dict = {'apiVersion': 'v1',
                              'kind': 'pool',
                              'metadata': {'cidr': str(ipv4_net.cidr)},
                              'spec': {'ipip': {'enabled': True}}
                              }

            ipv6_pool_dict = {'apiVersion': 'v1',
                              'kind': 'pool',
                              'metadata': {'cidr': str(ipv6_net.cidr)},
                              'spec': {}
                              }

            # Write out some yaml files to load in through calicoctl-go
            # We could have sent these via stdout into calicoctl, but this
            # seemed easier.
            with open('ipv4.yaml', 'w') as f:
                f.write(yaml.dump(ipv4_pool_dict, default_flow_style=False))
            with open('ipv6.yaml', 'w') as f:
                f.write(yaml.dump(ipv6_pool_dict, default_flow_style=False))
            # Create the ipv6 network using the Go calicoctl
            host.calicoctl("create -f ipv6.yaml", new=True)
            # And read it back out using the python calicoctl
            pool_out = host.calicoctl("pool show")
            # Assert output contains the ipv6 pool, but not the ipv4
            self.assertNotIn(str(ipv4_net), pool_out)
            self.assertIn(str(ipv6_net), pool_out)
            self.assertNotIn("ipip", pool_out)

            # Now read it out (yaml format) with the Go calicoctl too:
            pool_out = host.calicoctl("get pool --output=yaml", new=True)
            output = yaml.safe_load(pool_out)
            # Assert output is the same as the input
            self.assert_same([ipv6_pool_dict], output)

            # Add in the ipv4 network with Go calicoctl
            host.calicoctl("create -f ipv4.yaml", new=True)
            # And read it back out using the python calicoctl
            pool_out = host.calicoctl("pool show")
            # Assert output contains both the ipv4 pool and the ipv6
            self.assertIn(str(ipv4_net), pool_out)
            self.assertIn(str(ipv6_net), pool_out)
            self.assertIn("ipip", pool_out)

            # Now read it out with the Go calicoctl too:
            pool_out = host.calicoctl("get pool --output=yaml", new=True)
            output = yaml.safe_load(pool_out)
            # Assert output is a list: ipv4 pool followed by the ipv6 pool
            self.assert_same([ipv4_pool_dict, ipv6_pool_dict], output)

            # Remove both the ipv4 pool and ipv6 pool
            host.calicoctl("delete -f ipv6.yaml", new=True)
            host.calicoctl("delete -f ipv4.yaml", new=True)
            pool_out = host.calicoctl("pool show")
            # Assert output contains neither network
            self.assertNotIn(str(ipv4_net), pool_out)
            self.assertNotIn(str(ipv6_net), pool_out)
            self.assertNotIn("ipip", pool_out)
            # Now read it out with the Go calicoctl too:
            pool_out = host.calicoctl("get pool --output=yaml", new=True)
            output = yaml.safe_load(pool_out)
            self.assert_same([], output)

            # Assert that deleting the pool again fails.
            self.assertRaises(CommandExecError,
                              host.calicoctl, "delete -f ipv4.yaml", new=True)


class TestCommand(TestBase):
    """
    Test calicoctl create command
    """

    def test_create_from_file(self):
        """
        Test that json and yaml files can be used to create
        bgpPeer, hostEndpoint, policy, pool, profile objects.
        """
        # Define two bits of test data per type:
        testdata = {
            "bgpPeer": (
                {
                    'apiVersion': 'v1',
                    'kind': 'bgpPeer',
                    'metadata': {'hostname': 'Node1',
                                 'peerIP': '192.168.0.250',
                                 'scope': 'node'},
                    'spec': {'asNumber': 64514}
                },
                {
                    'apiVersion': 'v1',
                    'kind': 'bgpPeer',
                    'metadata': {'hostname': 'Node2',
                                 'peerIP': 'fd5f::6:ee',
                                 'scope': 'node'},
                    'spec': {'asNumber': 64590}
                }
            ),
            # "hostEndpoint": (
            #    {
            #        'apiVersion': 'v1',
            #        'kind': 'hostEndpoint',
            #        'metadata': {'hostname': 'host1',
            #                     'labels': {'type': 'database'},
            #                     'name': 'endpoint1'},
            #        'spec': {'interface': 'eth0',
            #                 'profiles': ['prof1',
            #                              'prof2']}
            #    },
            #    {
            #        'apiVersion': 'v1',
            #        'kind': 'hostEndpoint',
            #        'metadata': {'hostname': 'host2',
            #                     'labels': {'type': 'frontend'},
            #                     'name': 'endpoint2'},
            #        'spec': {'interface': 'cali7',
            #                 'profiles': ['prof1',
            #                              'prof2']}
            #    },
            # ),
            # "policy": (
            #     {'apiVersion': 'v1',
            #      'kind': 'policy',
            #      'metadata': {'name': 'policy1',
            #                   #'tier': 'tier1'
            #                   },
            #      'spec': {'egress': [{'action': 'deny',
            #                           'protocol': 'tcp',
            #                           'source': {
            #                               '!net': 'aa:bb:cc:ff::/100',
            #                               '!ports': [100],
            #                               '!selector': '',
            #                               '!tag': 'abcd'}}],
            #               'ingress': [{'action': 'nextTier',
            #                            'destination': {
            #                                'net': '10.20.30.40/32',
            #                                'ports': None,
            #                                'selector': '',
            #                                'tag': 'database'},
            #                            'icmp': {'code': 100,
            #                                     'type': 10},
            #                            'protocol': 'udp',
            #                            'source': {
            #                                'net': '1.2.0.0/16',
            #                                'ports': [1, 2, 3, 4],
            #                                'selector': '',
            #                                'tag': 'web'}}],
            #               'order': 6543215.321,
            #               'selector': ''}},
            #     {'apiVersion': 'v1',
            #      'kind': 'policy',
            #      'metadata': {'name': 'policy2',
            #                   #'tier': 'tier1'
            #                   },
            #      'spec': {'egress': [{'action': 'deny',
            #                           'protocol': 'tcp',
            #                           'source': {
            #                               '!net': 'aa:bb:cc::/100',
            #                               '!ports': [100],
            #                               '!selector': "",
            #                               '!tag': 'abcd'}}],
            #               'ingress': [{'action': 'nextTier',
            #                            'destination': {
            #                                'net': '10.20.30.40/32',
            #                                'ports': None,
            #                                'selector': "",
            #                                'tag': 'database'},
            #                            'icmp': {'code': 100,
            #                                     'type': 10},
            #                            'protocol': 'udp',
            #                            'source': {
            #                                'net': '1.2.3.0/24',
            #                                'ports': [1, 2, 3, 4],
            #                                'selector': "",
            #                                'tag': 'web'}}],
            #               'order': 100000,
            #               'selector': ""}},
            # ),
            "pool": (
                {'apiVersion': 'v1',
                 'kind': 'pool',
                 'metadata': {'cidr': "10.0.1.0/24"},
                 'spec': {'ipip': {'enabled': True}}
                 },
                {'apiVersion': 'v1',
                 'kind': 'pool',
                 'metadata': {'cidr': "10.0.2.0/24"},
                 'spec': {'ipip': {'enabled': True}}
                 },
            ),
            # "profile": (
            #     {'apiVersion': 'v1',
            #      'kind': 'profile',
            #      'metadata': {'name': 'profile1'},
            #      'spec': {'labels': {'type': 'database'},
            #               'rules': {
            #                   'egress': [{'action': 'deny'}],
            #                   'ingress': [{'action': 'deny'}]},
            #               'tags': ['a', 'b', 'c', 'a1']}
            #      },
            #     {'apiVersion': 'v1',
            #      'kind': 'profile',
            #      'metadata': {'name': 'profile2'},
            #      'spec': {'labels': {'type': 'frontend'},
            #               'rules': {
            #                   'egress': [{'action': 'deny'}],
            #                   'ingress': [{'action': 'deny'}]},
            #               'tags': ['a', 'b', 'c', 'a1']}
            #      },
            # )
        }
        with DockerHost('host', dind=False, start_calico=False) as host:
            for res in testdata.keys():
                logger.debug("Testing %s" % res)
                data1, data2 = testdata[res]
                # Write out the files to load later
                self.writeyaml('data1.yaml', data1)
                self.writejson('data2.json', data2)

                host.calicoctl("create -f data1.yaml", new=True)
                # Test use of create with stdin
                host.execute(
                    "cat data2.json | /code/dist/calicoctl create -f -")

                # Check both come out OK in yaml:
                self.check_data_in_datastore(
                    host, [data1, data2], res)

                # Check both come out OK in json:
                self.check_data_in_datastore(
                    host, [data1, data2], res, yaml_format=False)

    def test_apply_create_replace(self):
        """
        Basic check that apply, create and replace commands work correctly.
        """
        with DockerHost('host', dind=False, start_calico=False) as host:
            bgp_peer1 = {
                'apiVersion': 'v1',
                'kind': 'bgpPeer',
                'metadata': {'hostname': 'Node1',
                             'peerIP': '192.168.0.250',
                             'scope': 'node'},
                'spec': {'asNumber': 64514}
            }
            bgp_peer2 = {
                'apiVersion': 'v1',
                'kind': 'bgpPeer',
                'metadata': {'hostname': 'Node1',
                             'peerIP': '192.168.0.250',
                             'scope': 'node'},
                'spec': {'asNumber': 64590}
            }

            # Write test data files for loading later
            self.writeyaml('data1.yaml', bgp_peer1)
            self.writejson('data2.json', bgp_peer2)

            # apply - create when not present
            host.calicoctl("apply -f data1.yaml", new=True)
            # Check it went in OK
            self.check_data_in_datastore(host, [bgp_peer1], "bgpPeer")

            # create - skip overwrite with bgp_peer2
            host.calicoctl("create -f data2.json -s", new=True)
            # Check that nothing's changed
            self.check_data_in_datastore(host, [bgp_peer1], "bgpPeer")

            # replace - overwrite with bgp_peer2
            host.calicoctl("replace -f data2.json", new=True)
            # Check that we now have bgp_peer2 in the datastore
            self.check_data_in_datastore(host, [bgp_peer2], "bgpPeer")

            # apply - overwrite with bgp_peer1
            host.calicoctl("apply -f data1.yaml", new=True)
            # Check that we now have bgp_peer1 in the datastore
            self.check_data_in_datastore(host, [bgp_peer1], "bgpPeer")

            # delete
            host.calicoctl("delete -f data1.yaml", new=True)
            # Check it deleted
            self.check_data_in_datastore(host, [], "bgpPeer")

    def check_data_in_datastore(self, host, data, resource, yaml_format=True):
        if yaml_format:
            out = host.calicoctl(
                "get %s --output=yaml" % resource, new=True)
            output = yaml.safe_load(out)
        else:
            out = host.calicoctl(
                "get %s --output=json" % resource, new=True)
            output = json.loads(out)
        self.assert_same(data, output)

    @staticmethod
    def writeyaml(filename, data):
        with open(filename, 'w') as f:
            f.write(yaml.dump(data, default_flow_style=False))

    @staticmethod
    def writejson(filename, data):
        with open(filename, 'w') as f:
            f.write(json.dumps(data, sort_keys=True, indent=2,
                               separators=(',', ': ')))

