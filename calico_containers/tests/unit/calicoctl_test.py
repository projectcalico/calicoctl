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

import unittest
from StringIO import StringIO
from mock import patch, Mock, MagicMock, call
from nose_parameterized import parameterized
from netaddr import IPAddress, IPNetwork
from subprocess import CalledProcessError
from calico_ctl.bgp import *
from calico_ctl.bgp import validate_arguments as bgp_validate_arguments
from calico_ctl.endpoint import validate_arguments as ep_validate_arguments
from calico_ctl import node
from calico_ctl.node import validate_arguments as node_validate_arguments
from calico_ctl.pool import validate_arguments as pool_validate_arguments
from calico_ctl.profile import validate_arguments as profile_validate_arguments
from calico_ctl import container
from calico_ctl.container import validate_arguments as container_validate_arguments
from calico_ctl import utils
from calico_ctl.utils import validate_cidr, validate_ip, validate_characters
from pycalico.datastore_datatypes import BGPPeer, Endpoint, IPPool
from pycalico.datastore_errors import MultipleEndpointsMatch


class TestBgp(unittest.TestCase):

    @parameterized.expand([
        ({'<PEER_IP>':'127.a.0.1'}, True),
        ({'<PEER_IP>':'aa:bb::zz'}, True),
        ({'<AS_NUM>':9}, False),
        ({'<AS_NUM>':'9'}, False),
        ({'<AS_NUM>':'nine'}, True),
        ({'show':1, '--ipv4':1}, False)
    ])
    def test_validate_arguments(self, case, sys_exit_called):
        """
        Test validate_arguments for calicoctl bgp command
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            bgp_validate_arguments(case)

            # Assert that method exits on bad input
            self.assertEqual(m_sys_exit.called, sys_exit_called)

    @patch('calico_ctl.bgp.BGPPeer', autospec=True)
    @patch('calico_ctl.bgp.client', autospec=True)
    def test_bgp_peer_add(self, m_client, m_BGPPeer):
        """
        Test bgp_peer_add function for calico_ctl bgp
        """
        # Set up mock objects
        peer = Mock(spec=BGPPeer)
        m_BGPPeer.return_value = peer

        # Set up arguments
        address = '1.2.3.4'

        # Call method under test
        bgp_peer_add(address, 4, 1)

        # Assert
        m_BGPPeer.assert_called_once_with(IPAddress(address), 1)
        m_client.add_bgp_peer.assert_called_once_with(4, peer)

    @patch('calico_ctl.bgp.client', autospec=True)
    def test_bgp_peer_remove(self, m_client):
        """
        Test bgp_peer_remove function for calicoctl bgp
        """
        # Set up arguments
        address = '1.2.3.4'

        # Call method under test
        bgp_peer_remove(address, 4)

        # Assert
        m_client.remove_bgp_peer.assert_called_once_with(4, IPAddress(address))

    @patch('calico_ctl.bgp.client', autospec=True)
    def test_set_default_node_as(self, m_client):
        """
        Test set_default_node_as function for calicoctl bgp
        """
        # Call method under test
        set_default_node_as(1)

        # Assert
        m_client.set_default_node_as.assert_called_once_with(1)

    @patch('calico_ctl.bgp.client', autospec=True)
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_default_node_as(self, m_stdout, m_client):
        """
        Test for show_default_node_as() for calicoctl bgp
        """
        # Set up mock objects
        expected_return = '15'
        m_client.get_default_node_as.return_value = expected_return

        # Call method under test
        show_default_node_as()

        # Assert
        m_client.get_default_node_as.assert_called_once_with()
        self.assertEqual(m_stdout.getvalue().strip(), expected_return)

    @patch('calico_ctl.bgp.client', autospec=True)
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_bgp_node_mesh(self, m_stdout, m_client):
        """
        Test for show_bgp_node_mesh() for calicoctl bgp
        """
        # Set up mock objects
        expected_return = '15'
        m_client.get_bgp_node_mesh.return_value = expected_return

        # Call method under test
        show_bgp_node_mesh()

        # Assert
        m_client.get_bgp_node_mesh.assert_called_once_with()
        self.assertEqual(m_stdout.getvalue().strip(), 'on')

    @patch('calico_ctl.bgp.client', autospec=True)
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_bgp_node_mesh_fail(self, m_stdout, m_client):
        """
        Test for show_bgp_node_mesh() for calicoctl bgp
        """
        # Set up mock objects
        expected_return = ''
        m_client.get_bgp_node_mesh.return_value = expected_return

        # Call method under test
        show_bgp_node_mesh()

        # Assert
        m_client.get_bgp_node_mesh.assert_called_once_with()
        self.assertEqual(m_stdout.getvalue().strip(), 'off')

    @patch('calico_ctl.bgp.client', autospec=True)
    def test_set_bgp_node_mesh(self, m_client):
        """
        Test for set_bgp_node_mesh for calicoctl bgp
        """
        # Call method under test
        set_bgp_node_mesh(True)

        # Assert
        m_client.set_bgp_node_mesh.assert_called_once_with(True)


class TestContainer(unittest.TestCase):

    @parameterized.expand([
        ({'<CONTAINER>':'node1', 'ip':1, 'add':1, '<IP>':'127.a.0.1'}, True),
        ({'<CONTAINER>':'node1', 'ip':1, 'add':1, '<IP>':'aa:bb::zz'}, True),
        ({'add':1, '<CONTAINER>':'node1', '<IP>':'127.a.0.1'}, True),
        ({'add':1, '<CONTAINER>':'node1', '<IP>':'aa:bb::zz'}, True)
    ])
    def test_validate_arguments(self, case, sys_exit_called):
        """
        Test validate_arguments for calicoctl container command
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            container_validate_arguments(case)

            # Assert method exits if bad input
            self.assertEqual(m_sys_exit.called, sys_exit_called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_add(self, m_netns, m_get_pool_or_exit, m_client,
                           m_get_container_info_or_exit, m_enforce_root):
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_client.get_endpoint.side_effect = KeyError
        m_client.get_default_next_hops.return_value = 'next_hops'
        m_netns.set_up_endpoint.return_value = 'endpoint'

        # Call method under test
        test_return = container.container_add('container1', '1.1.1.1', 'interface')

        # Assert
        m_enforce_root.assert_called_once_with()
        m_get_container_info_or_exit.assert_called_once_with('container1')
        m_client.get_endpoint.assert_called_once_with(
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666
        )
        m_get_pool_or_exit.assert_called_once_with(IPAddress('1.1.1.1'))
        m_client.get_default_next_hops(node.hostname)
        m_netns.set_up_endpoint(
            ip='1.1.1.1',
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666,
            cpid='Pid_info',
            next_hop_ips='next_hops',
            veth_name='interface',
            proc_alias='/proc/'
        )
        m_client.set_endpoint.assert_called_once_with('endpoint')
        self.assertEqual(test_return, 'endpoint')

    @patch('sys.exit', autospec=True)
    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_add_existing_container(
            self, m_netns, m_get_pool_or_exit, m_client,
            m_get_container_info_or_exit, m_enforce_root, m_sys_exit):
        """
        Assert that the system exits when a container already exists
        """
        # Call method under test
        container.container_add('container1', '1.1.1.1', 'interface')

        # Assert
        m_sys_exit.assert_called_once_with(1)

    @patch('sys.exit', autospec=True)
    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_add_container_not_running(
            self, m_netns, m_get_pool_or_exit, m_client,
            m_get_container_info_or_exit, m_enforce_root, m_sys_exit):
        """
        Assert that system exits when a container is not running
        """
        # Set up mock object
        m_client.get_endpoint.side_effect = KeyError
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 0, 'Pid': 'Pid_info'}
        }

        # Call method under test
        container.container_add('container1', '1.1.1.1', 'interface')

        # Assert
        m_sys_exit.assert_called_once_with(1)

    @patch('sys.exit', autospec=True)
    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_add_not_ipv4_configured(
            self, m_netns, m_get_pool_or_exit, m_client,
            m_get_container_info_or_exit, m_enforce_root, m_sys_exit):
        """
        Assert that system exits when client cannot obtain next hop IPs
        """
        # Set up mock objects
        m_client.get_endpoint.side_effect = KeyError
        m_client.get_default_next_hops.return_value = {}

        # Call method under test
        container.container_add('container1', '1.1.1.1', 'interface')

        # Assert
        m_sys_exit.assert_called_once_with(1)

    @patch('sys.exit', autospec=True)
    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_add_ip_previously_assigned(
            self, m_netns, m_get_pool_or_exit, m_client,
            m_get_container_info_or_exit, m_enforce_root, m_sys_exit):
        """
        Assert that system exits when an ip address is already assigned in pool
        """
        # Set up mock object
        m_client.get_endpoint.side_effect = KeyError
        m_client.assign_address.return_value = []

        # Call method under test
        container.container_add('container1', '1.1.1.1', 'interface')

        # Assert
        m_sys_exit.assert_called_once_with(1)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_id', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_remove(self, m_netns, m_client,  m_get_container_id,
                              m_enforce_root):
        # Set up mock objects
        m_get_container_id.return_value = 666

        ipv4_nets = set()
        ipv4_nets.add(IPNetwork(IPAddress('1.1.1.1')))
        ipv6_nets = set()
        m_endpoint = MagicMock(spec=Endpoint)
        m_endpoint.ipv4_nets = ipv4_nets
        m_endpoint.ipv6_nets = ipv6_nets
        m_endpoint.endpoint_id = 12
        ippool = IPPool('1.1.1.1/24')
        m_client.get_endpoint.return_value = m_endpoint
        m_client.get_ip_pools.return_value = [ippool]

        # Call method under test
        container.container_remove('container1')

        # Assert
        m_enforce_root.assert_called_once_with()
        m_get_container_id.assert_called_once_with('container1')
        m_client.get_endpoint.assert_called_once_with(
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666
        )
        self.assertEqual(m_client.unassign_address.call_count, 1)
        m_netns.remove_endpoint.assert_called_once_with(12)
        m_client.remove_workload(node.hostname, utils.ORCHESTRATOR_ID, 666)

    @patch('sys.exit', autospec=True)
    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_id', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_remove_no_endpoint(self, m_netns, m_client,
                                          m_get_container_id, m_enforce_root,
                                          m_sys_exit):
        """
        Test that system exits when the client cannot obtain an endpoint
        """
        # Set up mock objects
        m_client.get_endpoint.side_effect = KeyError

        # Call function under test
        self.assertRaises(UnboundLocalError, container.container_remove, 'container1')

        # Assert sys.exit(1) was called
        m_sys_exit.assert_called_once_with(1)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_ipv4(self, m_netns, m_client, m_get_container_info_or_exit,
                              m_get_pool_or_exit, m_enforce_root):
        # Set up mock objects
        pool_return = 'pool'
        m_get_pool_or_exit.return_value = pool_return
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_endpoint = Mock()
        m_client.get_endpoint.return_value = m_endpoint

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        container.container_ip_add(container_name, ip, interface)

        # Assert
        m_enforce_root.assert_called_once_with()
        m_get_pool_or_exit.assert_called_once_with(IPAddress(ip))
        m_get_container_info_or_exit.assert_called_once_with(container_name)
        m_client.get_endpoint.assert_called_once_with(
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666
        )
        m_client.assign_address.assert_called_once_with(pool_return, ip)
        m_endpoint.ipv4_nets.add.assert_called_once_with(IPNetwork(IPAddress(ip)))
        m_client.update_endpoint.assert_called_once_with(m_endpoint)
        m_netns.add_ip_to_interface.assert_called_once_with(
            'Pid_info', IPAddress(ip), interface, proc_alias="/proc"
        )

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_ipv6(self, m_netns, m_client, m_get_container_info_or_exit,
                              m_get_pool_or_exit, m_enforce_root):
        # Set up mock objects
        pool_return = 'pool'
        m_get_pool_or_exit.return_value = pool_return
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_endpoint = Mock()
        m_client.get_endpoint.return_value = m_endpoint

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        container.container_ip_add(container_name, ip, interface)

        # Assert
        m_enforce_root.assert_called_once_with()
        m_get_pool_or_exit.assert_called_once_with(IPAddress(ip))
        m_get_container_info_or_exit.assert_called_once_with(container_name)
        m_client.get_endpoint.assert_called_once_with(
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666
        )
        m_client.assign_address.assert_called_once_with(pool_return, ip)
        m_endpoint.ipv6_nets.add.assert_called_once_with(IPNetwork(IPAddress(ip)))
        m_client.update_endpoint.assert_called_once_with(m_endpoint)
        m_netns.add_ip_to_interface.assert_called_once_with(
            'Pid_info', IPAddress(ip), interface, proc_alias="/proc"
        )

    @patch('sys.exit', autospec=True)
    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_container_not_running(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root, m_sys_exit):
        """
        Test that the system exits is the container is not running
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 0, 'Pid': 'Pid_info'}
        }

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        container.container_ip_add(container_name, ip, interface)

        # Assert
        m_sys_exit.assert_called_once_with(1)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_container_not_in_calico(
            self, m_netns, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test case when the container is not networked into calico
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_client.get_endpoint.return_value = Mock()
        m_client.get_endpoint.side_effect = KeyError

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)
        m_print_container_not_in_calico_msg.assert_called_once_with(container_name)
        self.assertFalse(m_client.assign_address.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_fail_assign_address(
            self, m_netns, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test case when the client tries to assign IP when address is already
        in the pool
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_client.assign_address.return_value = []

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_error_updating_datastore(
            self, m_netns, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test case when the client fails to update endpoint
        """
        # Set up mock objects
        m_get_pool_or_exit.return_value = 'pool'
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_client.update_endpoint.side_effect = KeyError

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)
        m_client.unassign_address.assert_called_once_with('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    @patch('calico_ctl.container.netns.add_ip_to_interface', autospec=True)
    def test_container_ip_add_netns_error_ipv4(
            self, m_netns, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test case when netns throws a CalledProcessError when trying to add ipv4
        to interface
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_get_pool_or_exit.return_value = 'pool'
        m_endpoint = Mock()
        m_client.get_endpoint.return_value = m_endpoint
        err = CalledProcessError(1, m_netns, "Error updating container")
        m_netns.side_effect = err

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)
        m_endpoint.ipv4_nets.remove.assert_called_once_with(
            IPNetwork(IPAddress(ip))
        )
        m_client.update_endpoint.assert_has_calls([
            call(m_endpoint), call(m_endpoint)])
        m_client.unassign_address('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    @patch('calico_ctl.container.netns.add_ip_to_interface', autospec=True)
    def test_container_ip_add_netns_error_ipv6(
            self, m_netns, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test case when netns throws a CalledProcessError when trying to add ipv6
        to interface
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_get_pool_or_exit.return_value = 'pool'
        m_endpoint = Mock()
        m_client.get_endpoint.return_value = m_endpoint
        err = CalledProcessError(1, m_netns, "Error updating container")
        m_netns.side_effect = err

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)
        m_endpoint.ipv6_nets.remove.assert_called_once_with(
            IPNetwork(IPAddress(ip))
        )
        m_client.update_endpoint.assert_has_calls([
            call(m_endpoint), call(m_endpoint)])
        m_client.unassign_address('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_ipv4(self, m_netns, m_client,
            m_get_container_info_or_exit, m_get_pool_or_exit, m_enforce_root):
        # Set up mock objects
        m_get_pool_or_exit.return_value = 'pool'
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        ipv4_nets = set()
        ipv4_nets.add(IPNetwork(IPAddress('1.1.1.1')))
        m_endpoint = Mock(spec=Endpoint)
        m_endpoint.ipv4_nets = ipv4_nets
        m_client.get_endpoint.return_value = m_endpoint
        print "m_endpoint is %s" % m_endpoint.ipv4_nets.__class__

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test
        container.container_ip_remove(container_name, ip, interface)

        # Assert
        m_enforce_root.assert_called_once_with()
        m_get_pool_or_exit.assert_called_once_with(IPAddress(ip))
        m_get_container_info_or_exit.assert_called_once_with(container_name)
        m_client.get_endpoint.assert_called_once_with(
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666
        )
        m_client.update_endpoint.assert_called_once_with(m_endpoint)
        m_netns.remove_ip_from_interface(
            'Pid_info',
            IPAddress(ip),
            interface,
            proc_alias="/proc"
        )
        m_client.unassign_address('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_ipv6(self, m_netns, m_client,
            m_get_container_info_or_exit, m_get_pool_or_exit, m_enforce_root):
        # Set up mock objects
        m_get_pool_or_exit.return_value = 'pool'
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        ipv6_nets = set()
        ipv6_nets.add(IPNetwork(IPAddress('1::1')))
        m_endpoint = Mock(spec=Endpoint)
        m_endpoint.ipv6_nets = ipv6_nets
        m_client.get_endpoint.return_value = m_endpoint

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        container.container_ip_remove(container_name, ip, interface)

        # Assert
        m_enforce_root.assert_called_once_with()
        m_get_pool_or_exit.assert_called_once_with(IPAddress(ip))
        m_get_container_info_or_exit.assert_called_once_with(container_name)
        m_client.get_endpoint.assert_called_once_with(
            hostname=node.hostname,
            orchestrator_id=utils.ORCHESTRATOR_ID,
            workload_id=666
        )
        m_client.update_endpoint.assert_called_once_with(m_endpoint)
        m_netns.remove_ip_from_interface(
            'Pid_info',
            IPAddress(ip),
            interface,
            proc_alias="/proc"
        )
        m_client.unassign_address('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_not_running(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test that the system exits is the container is not running
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 0, 'Pid': 'Pid_info'}
        }

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_ip_not_assigned(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test case when Ip address is not assigned to container
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        ipv6_nets = set()
        m_endpoint = Mock(spec=Endpoint)
        m_endpoint.ipv6_nets = ipv6_nets
        m_client.get_endpoint.return_value = m_endpoint

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_container_not_on_calico(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test case when container is not networked into Calico
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_client.get_endpoint.side_effect = KeyError

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_fail_updating_datastore(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test case when client fails on updating endpoint in datastore
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        ipv6_nets = set()
        ipv6_nets.add(IPNetwork(IPAddress('1::1')))
        m_endpoint = Mock(spec=Endpoint)
        m_endpoint.ipv6_nets = ipv6_nets
        m_client.get_endpoint.return_value = m_endpoint
        m_client.update_endpoint.side_effect = KeyError

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_netns_error(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test case when client fails on removing ip from interface through netns
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        ipv6_nets = set()
        ipv6_nets.add(IPNetwork(IPAddress('1::1')))
        m_endpoint = Mock(spec=Endpoint)
        m_endpoint.ipv6_nets = ipv6_nets
        m_client.get_endpoint.return_value = m_endpoint
        err = CalledProcessError(1, m_netns, "Error removing ip")
        m_netns.remove_ip_from_interface.side_effect = err

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)


class TestEndpoint(unittest.TestCase):

    @parameterized.expand([
        ({'<PROFILES>':['profile-1', 'profile-2', 'profile-3']}, False),
        ({'<PROFILES>':['Profile1', 'Profile!']}, True),
        ({}, False)
    ])
    def test_validate_arguments(self, case, sys_exit_called):
        """
        Test validate_arguments for calicoctl endpoint command
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            ep_validate_arguments(case)

            # Assert method exits if bad input
            self.assertEqual(m_sys_exit.called, sys_exit_called)


class TestNode(unittest.TestCase):

    @parameterized.expand([
        ({'--ip':'127.a.0.1'}, True),
        ({'--ip':'aa:bb::cc'}, True),
        ({'--ip':'127.0.0.1', '--ip6':'127.0.0.1'}, True),
        ({'--ip':'127.0.0.1', '--ip6':'aa:bb::zz'}, True)
    ])
    def test_validate_arguments(self, case, sys_exit_called):
        """
        Test validate_arguments for calicoctl node command
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            node_validate_arguments(case)

            # Assert that method exits on bad input
            self.assertEqual(m_sys_exit.called, sys_exit_called)


class TestPool(unittest.TestCase):

    @parameterized.expand([
        ({'add':1, '<CIDRS>':['127.a.0.1']}, True),
        ({'add':1, '<CIDRS>':['aa:bb::zz']}, True),
        ({'add':1, '<CIDRS>':['1.2.3.4']}, False),
        ({'add':1, '<CIDRS>':['1.2.3.0/24', '8.8.0.0/16']}, False),
        ({'add':1, '<CIDRS>':['aa:bb::ff']}, False),
        ({'range':1, 'add':1, '<START_IP>':'1.2.3.0',
          '<END_IP>':'1.2.3.255'}, False),
        ({'range':1, 'add':1, '<START_IP>':'1.2.3.255',
          '<END_IP>':'1.2.3.1'}, True),
        ({'range':1, 'add':1, '<START_IP>':'1.2.3.0',
          '<END_IP>':'bad'}, True),
        ({'range':1, 'add':1, '<START_IP>':'bad',
          '<END_IP>':'1.2.3.1'}, True),
        ({'range':1, 'add':1, '<START_IP>':'1.2.3.255',
          '<END_IP>':'aaaa::'}, True),
    ])
    def test_validate_arguments(self, case, sys_exit_called):
        """
        Test validate_arguments for calicoctl pool command
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            pool_validate_arguments(case)

            # Call method under test for each test case
            self.assertEqual(m_sys_exit.called, sys_exit_called)


class TestProfile(unittest.TestCase):

    @parameterized.expand([
        ({'<PROFILE>':'profile-1'}, False),
        ({'<PROFILE>':'Profile!'}, True),
        ({'<SRCTAG>':'Tag-1', '<DSTTAG>':'Tag-2'}, False),
        ({'<SRCTAG>':'Tag~1', '<DSTTAG>':'Tag~2'}, True),
        ({'<SRCCIDR>':'127.a.0.1'}, True),
        ({'<DSTCIDR>':'aa:bb::zz'}, True),
        ({'<SRCCIDR>':'1.2.3.4', '<DSTCIDR>':'1.2.3.4'}, False),
        ({'<ICMPCODE>':'5'}, False),
        ({'<ICMPTYPE>':'16'}, False),
        ({'<ICMPCODE>':100, '<ICMPTYPE>':100}, False),
        ({'<ICMPCODE>':4, '<ICMPTYPE>':255}, True),
        ({}, False)
    ])
    def test_validate_arguments(self, case, sys_exit_called):
        """
        Test validate_arguments for calicoctl profile command
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            profile_validate_arguments(case)

            # Assert that method exits on bad input
            self.assertEqual(m_sys_exit.called, sys_exit_called)


class TestUtils(unittest.TestCase):

    @parameterized.expand([
        ('127.a.0.1', False),
        ('aa:bb::zz', False),
        ('1.2.3.4', True),
        ('1.2.3.0/24', True),
        ('aa:bb::ff', True),
        ('1111:2222:3333:4444:5555:6666:7777:8888', True),
        ('4294967295', False)
    ])
    def test_validate_cidr(self, cidr, expected_result):
        """
        Test validate_cidr function in calico_ctl utils
        """
        # Call method under test
        test_result = validate_cidr(cidr)

        # Assert
        self.assertEqual(expected_result, test_result)

    @parameterized.expand([
        ('1.2.3.4', 4, True),
        ('1.2.3.4', 6, False),
        ('1.2.3.4', 4, True),
        ('1.2.3.0/24', 4, False),
        ('aa:bb::ff', 4, False),
        ('aa:bb::ff', 6, True),
        ('1111:2222:3333:4444:5555:6666:7777:8888', 6, True),
        ('4294967295', 4, True),
        ('5000000000', 4, False)
    ])
    def test_validate_ip(self, ip, version, expected_result):
        """
        Test validate_ip function in calico_ctl utils
        """
        # Call method under test
        test_result = validate_ip(ip, version)

        # Assert
        self.assertEqual(expected_result, test_result)

    @parameterized.expand([
        ('abcdefghijklmnopqrstuvwxyz', True),
        ('0123456789', True),
        ('profile_1', True),
        ('profile-1', True),
        ('profile 1', False),
        ('profile.1', True),
        ('!', False),
        ('@', False),
        ('#', False),
        ('$', False),
        ('%', False),
        ('^', False),
        ('&', False),
        ('*', False),
        ('()', False)
    ])
    def test_validate_characters(self, input_string, expected_result):
        """
        Test validate_characters function in calico_ctl utils
        """
        with patch('sys.exit', autospec=True) as m_sys_exit:
            # Call method under test
            test_result = validate_characters(input_string)

            # Assert expected result
            self.assertEqual(expected_result, test_result)
