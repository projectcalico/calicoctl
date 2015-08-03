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
from requests import Response
from StringIO import StringIO

from docker.errors import APIError
from mock import patch, Mock, call, ANY
from nose_parameterized import parameterized
from netaddr import IPAddress, IPNetwork
from subprocess import CalledProcessError

from sh import Command, CommandNotFound
from calico_ctl.bgp import *
from calico_ctl.bgp import validate_arguments as bgp_validate_arguments
from calico_ctl import diags
from calico_ctl.endpoint import validate_arguments as ep_validate_arguments
from calico_ctl import node
from calico_ctl.node import validate_arguments as node_validate_arguments
from calico_ctl.pool import validate_arguments as pool_validate_arguments
from calico_ctl.profile import validate_arguments as profile_validate_arguments
from calico_ctl import container
from calico_ctl.container import validate_arguments as container_validate_arguments
from calico_ctl import utils
from calico_ctl.utils import (validate_cidr, validate_ip, validate_characters,
                              validate_hostname_port)
from pycalico.datastore_datatypes import BGPPeer, Endpoint, IPPool
from pycalico.datastore import (ETCD_AUTHORITY_ENV,
                                ETCD_AUTHORITY_DEFAULT)
from pycalico.datastore import DatastoreClient
from etcd import EtcdResult, EtcdException, Client


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
        """
        Test container_add method of calicoctl container command
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'},
            'HostConfig': {'NetworkMode': "not host"}
        }
        m_client.get_endpoint.side_effect = KeyError
        m_client.get_default_next_hops.return_value = 'next_hops'

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
        m_client.get_default_next_hops.assert_called_once_with(node.hostname)

        # Check an enpoint object was returned
        self.assertTrue(isinstance(test_return, Endpoint))

        self.assertTrue(m_netns.create_veth.called)
        self.assertTrue(m_netns.move_veth_into_ns.called)
        self.assertTrue(m_netns.add_ip_to_ns_veth.called)
        self.assertTrue(m_netns.add_ns_default_route.called)
        self.assertTrue(m_netns.get_ns_veth_mac.called)
        self.assertTrue(m_client.set_endpoint.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    def test_container_add_container_host_ns(self, m_client,
                         m_get_container_info_or_exit, m_enforce_root):
        """
        Test container_add method of calicoctl container command when the
        container shares the host namespace.
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'},
            'HostConfig': {'NetworkMode': 'host'}
        }
        m_client.get_endpoint.side_effect = KeyError

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_add,
                          'container1', '1.1.1.1', 'interface')
        m_enforce_root.assert_called_once_with()

class TestDiags(unittest.TestCase):

    @patch('calico_ctl.diags.tempfile', autospec=True)
    @patch('os.mkdir', autospec=True)
    @patch('os.path.isdir', autospec=True)
    @patch('calico_ctl.diags.datetime', autospec=True)
    @patch('__builtin__.open', autospec=True)
    @patch('socket.gethostname', autospec=True)
    @patch('sh.Command._create', spec=Command)
    @patch('calico_ctl.diags.copytree', autospec=True)
    @patch('tarfile.open', autospec=True)
    @patch('calico_ctl.diags.DatastoreClient', autospec=True)
    @patch('calico_ctl.diags.upload_temp_diags', autospec=True)
    @patch('calico_ctl.diags.subprocess', autospec=True)
    def test_save_diags(self, m_subprocess, m_upload_temp_diags,
                        m_DatastoreClient, m_tarfile_open, m_copytree,
                        m_sh_command, m_socket, m_open, m_datetime,
                        os_path_isdir, m_os_mkdir, m_tempfile):
        """
        Test save_diags for calicoctl diags command
        """
        # Set up mock objects
        m_tempfile.mkdtemp.return_value = '/temp/dir'
        date_today = '2015-7-24_09_05_00'
        m_datetime.strftime.return_value = date_today
        m_socket.return_value = 'hostname'
        m_sh_command_return = Mock(autospec=True)
        m_sh_command.return_value = m_sh_command_return
        m_datetime.today.return_value = 'diags-07242015_090500.tar.gz'
        m_os_mkdir.return_value = True
        # The DatastoreClient contains an etcd Client
        # The etcd Client reads in a list of children of type EtcdResult
        # The children are accessed by calling get_subtree method on the etcd Client
        m_datastore_client = Mock(spec=DatastoreClient)
        m_datastore_client.etcd_client = Mock(spec=Client)
        m_datastore_data = Mock(spec=EtcdResult)
        m_child_1 = EtcdResult(node={'dir': True, 'key': 666})
        m_child_2 = EtcdResult(node={'key': 555, 'value': 999})
        m_datastore_data.get_subtree.return_value = [m_child_1, m_child_2]
        m_datastore_client.etcd_client.read.return_value = m_datastore_data
        m_DatastoreClient.return_value = m_datastore_client

        # Set up arguments
        log_dir = '/log/dir'
        temp_dir = '/temp/dir/'
        diags_dir = temp_dir + 'diagnostics'

        # Call method under test
        diags.save_diags(log_dir, upload=True)

        # Assert
        m_subprocess.call.assert_called_once_with(
            ["docker", "exec", "calico-node", "pkill", "-SIGUSR1", "felix"])
        m_tempfile.mkdtemp.assert_called_once_with()
        m_os_mkdir.assert_called_once_with(diags_dir)
        m_open.assert_has_calls([
            call(diags_dir + '/date', 'w'),
            call().__enter__().write('DATE=%s' % date_today),
            call(diags_dir + '/hostname', 'w'),
            call().__enter__().write('hostname'),
            call(diags_dir + '/netstat', 'w'),
            call().__enter__().writelines(m_sh_command_return()),
            call(diags_dir + '/route', 'w'),
            call().__enter__().write('route --numeric\n'),
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().write('ip route\n'),
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().write('ip -6 route\n'),
            call().__enter__().writelines(m_sh_command_return()),
            call(diags_dir + '/iptables', 'w'),
            call().__enter__().writelines(m_sh_command_return()),
            call(diags_dir + '/ipset', 'w'),
            call().__enter__().writelines(m_sh_command_return()),
            call(diags_dir + '/etcd_calico', 'w'),
            call().__enter__().write('dir?, key, value\n'),
            call().__enter__().write('DIR,  666,\n'),
            call().__enter__().write('FILE, 555, 999\n')
        ], any_order=True)
        m_sh_command.assert_has_calls([
            call('netstat'),
            call()(all=True, numeric=True),
            call('route'),
            call()(numeric=True),
            call('ip'),
            call()('route'),
            call()('-6', 'route'),
            call('iptables-save'),
            call()(),
            call('ipset'),
            call()('list')
        ])
        m_datastore_client.etcd_client.read.assert_called_once_with('/calico', recursive=True)
        m_copytree.assert_called_once_with(log_dir, diags_dir + '/logs', ignore=ANY)
        m_tarfile_open.assert_called_once_with(temp_dir + date_today, 'w:gz')
        m_upload_temp_diags.assert_called_once_with(temp_dir + date_today)

    @patch('calico_ctl.diags.tempfile', autospec=True)
    @patch('os.mkdir', autospec=True)
    @patch('os.path.isdir', autospec=True)
    @patch('calico_ctl.diags.datetime', autospec=True)
    @patch('__builtin__.open', autospec=True)
    @patch('socket.gethostname', autospec=True)
    @patch('sh.Command._create', spec=Command)
    @patch('calico_ctl.diags.copytree', autospec=True)
    @patch('tarfile.open', autospec=True)
    @patch('calico_ctl.diags.DatastoreClient', autospec=True)
    @patch('calico_ctl.diags.subprocess', autospec=True)
    def test_save_diags_exceptions(
            self, m_subprocess, m_DatastoreClient, m_tarfile_open, m_copytree,
            m_sh_command, m_socket, m_open, m_datetime, m_os_path_isdir,
            m_os_mkdir, m_tempfile):
        """
        Test all exception cases save_diags method in calicoctl diags command

        Raise CommandNotFound when sh.Command._create is called
        Raise EtcdException when trying to read from the etcd datastore
        Return false when trying to read logs from log directory
        """
        # Set up mock objects
        m_tempfile.mkdtemp.return_value = '/temp/dir'
        date_today = '2015-7-24_09_05_00'
        m_datetime.strftime.return_value = date_today
        m_socket.return_value = 'hostname'
        m_sh_command_return = Mock(autospec=True)
        m_sh_command.return_value = m_sh_command_return
        m_sh_command.side_effect= CommandNotFound
        m_os_path_isdir.return_value = False
        m_datastore_client = Mock(spec=DatastoreClient)
        m_datastore_client.etcd_client = Mock(spec=Client)
        m_datastore_client.etcd_client.read.side_effect = EtcdException
        m_DatastoreClient.return_value = m_datastore_client

        # Set up arguments
        log_dir = '/log/dir'
        temp_dir = '/temp/dir/'
        diags_dir = temp_dir + 'diagnostics'

        # Call method under test
        diags.save_diags(log_dir, upload=False)

        # Assert
        m_subprocess.call.assert_called_once_with(
            ["docker", "exec", "calico-node", "pkill", "-SIGUSR1", "felix"])
        m_open.assert_has_calls([
            call(diags_dir + '/date', 'w'),
            call().__enter__().write('DATE=%s' % date_today),
            call(diags_dir + '/hostname', 'w'),
            call().__enter__().write('hostname'),
            call(diags_dir + '/netstat', 'w'),
            call(diags_dir + '/route', 'w'),
            call(diags_dir + '/iptables', 'w'),
            call(diags_dir + '/ipset', 'w'),
        ], any_order=True)
        self.assertNotIn([
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().write('route --numeric\n'),
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().write('ip route\n'),
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().write('ip -6 route\n'),
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().writelines(m_sh_command_return()),
            call().__enter__().writelines(m_sh_command_return()),
            call(diags_dir + '/etcd_calico', 'w'),
            call().__enter__().write('dir?, key, value\n'),
            call().__enter__().write('DIR,  666,\n'),
            call().__enter__().write('FILE, 555, 999\n')
        ], m_open.mock_calls)
        self.assertFalse(m_copytree.called)
        m_tarfile_open.assert_called_once_with(temp_dir + date_today, 'w:gz')


class TestEndpoint(unittest.TestCase):

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    def test_container_add_existing_container(
            self, m_get_pool_or_exit, m_client, m_get_container_info_or_exit,
            m_enforce_root):
        """
        Test container_add when a container already exists.

        Do not raise an exception when the client tries 'get_endpoint'
        Assert that the system then exits and all expected calls are made
        """
        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_add,
                          'container1', '1.1.1.1', 'interface')

        # Assert only expected calls were made
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertFalse(m_get_pool_or_exit.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    def test_container_add_container_not_running(
            self, m_get_pool_or_exit, m_client,
            m_get_container_info_or_exit, m_enforce_root):
        """
        Test container_add when a container is not running

        get_container_info_or_exit returns a running state of value 0
        Assert that the system then exits and all expected calls are made
        """
        # Set up mock object
        m_client.get_endpoint.side_effect = KeyError
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 0, 'Pid': 'Pid_info'}
        }

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_add,
                          'container1', '1.1.1.1', 'interface')

        # Assert only expected calls were made
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertFalse(m_get_pool_or_exit.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    def test_container_add_not_ipv4_configured(
            self, m_get_pool_or_exit, m_client, m_get_container_info_or_exit,
            m_enforce_root):
        """
        Test container_add when the client cannot obtain next hop IPs

        client.get_default_next_hops returns an empty dictionary, which produces
        a KeyError when trying to determine the IP.
        Assert that the system then exits and all expected calls are made
        """
        # Set up mock objects
        m_client.get_endpoint.side_effect = KeyError
        m_client.get_default_next_hops.return_value = {}

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_add,
                          'container1', '1.1.1.1', 'interface')

        # Assert only expected calls were made
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_client.get_default_next_hops.called)
        self.assertFalse(m_client.assign_address.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_add_ip_previously_assigned(
            self, m_netns, m_get_pool_or_exit, m_client,
            m_get_container_info_or_exit, m_enforce_root):
        """
        Test container_add when an ip address is already assigned in pool

        client.assign_address returns an empty list.
        Assert that the system then exits and all expected calls are made
        """
        # Set up mock object
        m_client.get_endpoint.side_effect = KeyError
        m_client.assign_address.return_value = []

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_add,
                          'container1', '1.1.1.1', 'interface')

        # Assert only expected calls were made
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_client.get_default_next_hops.called)
        self.assertTrue(m_client.assign_address.called)
        self.assertFalse(m_netns.create_veth.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_id', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_remove(self, m_netns, m_client,  m_get_container_id,
                              m_enforce_root):
        """
        Test for container_remove of calicoctl container command
        """
        # Set up mock objects
        m_get_container_id.return_value = 666
        ipv4_nets = set()
        ipv4_nets.add(IPNetwork(IPAddress('1.1.1.1')))
        ipv6_nets = set()
        m_endpoint = Mock(spec=Endpoint)
        m_endpoint.ipv4_nets = ipv4_nets
        m_endpoint.ipv6_nets = ipv6_nets
        m_endpoint.endpoint_id = 12
        m_endpoint.name = "eth1234"
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
        m_netns.remove_veth.assert_called_once_with("eth1234")
        m_client.remove_workload.assert_called_once_with(
            node.hostname, utils.ORCHESTRATOR_ID, 666)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_container_id', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    def test_container_remove_no_endpoint(
            self, m_client, m_get_container_id, m_enforce_root):
        """
        Test for container_remove when the client cannot obtain an endpoint

        client.get_endpoint raises a KeyError.
        Assert that the system then exits and all expected calls are made
        """
        # Set up mock objects
        m_client.get_endpoint.side_effect = KeyError

        # Call function under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_remove, 'container1')

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_container_id.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertFalse(m_client.get_ip_pools.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_ipv4(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_add with an ipv4 ip argument

        Assert that the correct calls associated with an ipv4 address are made
        """
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
        m_netns.add_ip_to_ns_veth.assert_called_once_with(
            'Pid_info', IPAddress(ip), interface
        )

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_ipv6(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_add with an ipv6 ip argument

        Assert that the correct calls associated with an ipv6 address are made
        """
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
        m_netns.add_ip_to_ns_veth.assert_called_once_with(
            'Pid_info', IPAddress(ip), interface
        )

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client.get_endpoint', autospec=True)
    def test_container_ip_add_container_not_running(
            self, m_client_get_endpoint, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_add when the container is not running

        get_container_info_or_exit returns a running state of value 0.
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertFalse(m_client_get_endpoint.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    def test_container_ip_add_container_not_in_calico(
            self, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_add when the container is not networked into calico

        client.get_endpoint raises a KeyError.
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a System Exit
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        m_print_container_not_in_calico_msg.assert_called_once_with(container_name)
        self.assertFalse(m_client.assign_address.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_add_fail_assign_address(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_add when the client cannot assign an IP

        client.assign_address returns an empty list.
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertFalse(m_netns.add_ip_to_ns_veth.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns.add_ip_to_ns_veth', autospec=True)
    def test_container_ip_add_error_updating_datastore(
            self, m_netns_add_ip_to_ns_veth, m_client,
            m_get_container_info_or_exit, m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_add when the client fails to update endpoint

        client.update_endpoint raises a KeyError.
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_client.assign_address.called)
        m_client.unassign_address.assert_called_once_with('pool', ip)
        self.assertFalse(m_netns_add_ip_to_ns_veth.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns.add_ip_to_ns_veth', autospec=True)
    def test_container_ip_add_netns_error_ipv4(
            self, m_netns_add_ip_to_ns_veth, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test container_ip_add when netns cannot add an ipv4 to interface

        netns.add_ip_to_ns_veth throws a CalledProcessError.
        Assert that the system then exits and all expected calls are made
        """
        # Set up mock objects
        m_get_container_info_or_exit.return_value = {
            'Id': 666,
            'State': {'Running': 1, 'Pid': 'Pid_info'}
        }
        m_get_pool_or_exit.return_value = 'pool'
        m_endpoint = Mock()
        m_client.get_endpoint.return_value = m_endpoint
        err = CalledProcessError(
            1, m_netns_add_ip_to_ns_veth, "Error updating container")
        m_netns_add_ip_to_ns_veth.side_effect = err

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1.1.1.1'
        interface = 'interface'

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_add,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_client.assign_address.called)
        self.assertTrue(m_netns_add_ip_to_ns_veth.called)
        m_endpoint.ipv4_nets.remove.assert_called_once_with(
            IPNetwork(IPAddress(ip))
        )
        m_client.update_endpoint.assert_has_calls([
            call(m_endpoint), call(m_endpoint)])
        m_client.unassign_address.assert_called_once_with('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.print_container_not_in_calico_msg', autospec=True)
    @patch('calico_ctl.container.netns.add_ip_to_ns_veth', autospec=True)
    def test_container_ip_add_netns_error_ipv6(
            self, m_netns, m_print_container_not_in_calico_msg, m_client,
            m_get_container_info_or_exit,  m_get_pool_or_exit, m_enforce_root):
        """
        Test container_ip_add when netns cannot add an ipv6 to interface

        netns.add_ip_to_ns_veth throws a CalledProcessError.
        Assert that the system then exits and all expected calls are made
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

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_client.assign_address.called)
        self.assertTrue(m_netns.called)
        m_endpoint.ipv6_nets.remove.assert_called_once_with(
            IPNetwork(IPAddress(ip))
        )
        m_client.update_endpoint.assert_has_calls([
            call(m_endpoint), call(m_endpoint)])
        m_client.unassign_address.assert_called_once_with('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_ipv4(self, m_netns, m_client,
            m_get_container_info_or_exit, m_get_pool_or_exit, m_enforce_root):
        """
        Test container_ip_remove with an ipv4 ip argument
        """
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
        m_netns.remove_ip_from_ns_veth.assert_called_once_with(
            'Pid_info',
            IPAddress(ip),
            interface
        )
        m_client.unassign_address.assert_called_once_with('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_ipv6(self, m_netns, m_client,
            m_get_container_info_or_exit, m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_remove with an ipv6 ip argument
        """
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
        m_netns.remove_ip_from_ns_veth.assert_called_once_with(
            'Pid_info',
            IPAddress(ip),
            interface
        )
        m_client.unassign_address.assert_called_once_with('pool', ip)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    def test_container_ip_remove_not_running(
            self, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test for container_ip_remove when the container is not running

        get_container_info_or_exit returns a running state of value 0.
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertFalse(m_client.get_endpoint.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    def test_container_ip_remove_ip_not_assigned(
            self, m_client, m_get_container_info_or_exit, m_get_pool_or_exit,
            m_enforce_root):
        """
        Test container_ip_remove when an IP address is not assigned to a container

        client.get_endpoint returns an endpoint with no ip nets
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertFalse(m_client.update_endpoint.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    def test_container_ip_remove_container_not_on_calico(
            self, m_client, m_get_container_info_or_exit, m_get_pool_or_exit,
            m_enforce_root):
        """
        Test for container_ip_remove when container is not networked into Calico

        client.get_endpoint raises a KeyError
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertFalse(m_client.update_endpoint.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_fail_updating_datastore(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test container_ip_remove when client fails to update endpoint in datastore

        client.update_endpoint throws a KeyError
        Assert that the system then exits and all expected calls are made
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

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_client.update_endpoint.called)
        self.assertFalse(m_netns.remove_ip_from_ns_veth.called)

    @patch('calico_ctl.container.enforce_root', autospec=True)
    @patch('calico_ctl.container.get_pool_or_exit', autospec=True)
    @patch('calico_ctl.container.get_container_info_or_exit', autospec=True)
    @patch('calico_ctl.container.client', autospec=True)
    @patch('calico_ctl.container.netns', autospec=True)
    def test_container_ip_remove_netns_error(
            self, m_netns, m_client, m_get_container_info_or_exit,
            m_get_pool_or_exit, m_enforce_root):
        """
        Test container_ip_remove when client fails on removing ip from interface

        netns.remove_ip_from_ns_veth raises a CalledProcessError
        Assert that the system then exits and all expected calls are made
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
        m_netns.remove_ip_from_ns_veth.side_effect = err

        # Set up arguments to pass to method under test
        container_name = 'container1'
        ip = '1::1'
        interface = 'interface'

        # Call method under test expecting a SystemExit
        self.assertRaises(SystemExit, container.container_ip_remove,
                          container_name, ip, interface)

        # Assert
        self.assertTrue(m_enforce_root.called)
        self.assertTrue(m_get_pool_or_exit.called)
        self.assertTrue(m_get_container_info_or_exit.called)
        self.assertTrue(m_client.get_endpoint.called)
        self.assertTrue(m_client.update_endpoint.called)
        self.assertTrue(m_netns.remove_ip_from_ns_veth.called)
        self.assertFalse(m_client.unassign_address.called)

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


    @patch('os.path.exists', autospec=True)
    @patch('os.makedirs', autospec=True)
    @patch('os.getenv', autospec= True)
    @patch('calico_ctl.node.check_system', autospec=True)
    @patch('calico_ctl.node.get_host_ips', autospec=True)
    @patch('calico_ctl.node.warn_if_unknown_ip', autospec=True)
    @patch('calico_ctl.node.warn_if_hostname_conflict', autospec=True)
    @patch('calico_ctl.node.install_kubernetes', autospec=True)
    @patch('calico_ctl.node.client', autospec=True)
    @patch('calico_ctl.node.docker_client', autospec=True)
    @patch('calico_ctl.node.docker', autospec=True)
    @patch('calico_ctl.node._find_or_pull_node_image', autospec=True)
    @patch('calico_ctl.node._attach_and_stream', autospec=True)
    def test_node_start(self, m_attach_and_stream,
                        m_find_or_pull_node_image, m_docker,
                        m_docker_client, m_client, m_install_kube,
                        m_warn_if_hostname_conflict, m_warn_if_unknown_ip,
                        m_get_host_ips, m_check_system, m_os_getenv,
                        m_os_makedirs, m_os_path_exists):
        """
        Test that the node_start function behaves as expected by mocking
        function returns
        """
        # Set up mock objects
        m_os_path_exists.return_value = False
        ip_1 = '1.1.1.1'
        ip_2 = '2.2.2.2'
        m_get_host_ips.return_value = [ip_1, ip_2]
        m_os_getenv.side_effect = iter(['1.1.1.1:80', ""])
        m_docker.utils.create_host_config.return_value = 'host_config'
        container = {'Id':666}
        m_docker_client.create_container.return_value = container

        # Set up arguments
        node_image = 'node_image'
        log_dir = './log_dir'
        ip = ''
        ip6 = 'aa:bb::zz'
        as_num = ''
        detach = False
        kubernetes = True

        # Call method under test
        node.node_start(
            node_image, log_dir, ip, ip6, as_num, detach, kubernetes
        )

        # Set up variables used in assertion statements
        environment = [
            "HOSTNAME=%s" % node.hostname,
            "IP=%s" % ip_2,
            "IP6=%s" % ip6,
            "ETCD_AUTHORITY=1.1.1.1:80",  # etcd host:port
            "FELIX_ETCDADDR=1.1.1.1:80",  # etcd host:port
            "POLICY_ONLY_CALICO=",
        ]
        binds = {
            "/proc":
                {
                    "bind": "/proc_host",
                    "ro": False
                },
            log_dir:
                {
                    "bind": "/var/log/calico",
                    "ro": False
                },
            "/run/docker/plugins":
                {
                    "bind": "/usr/share/docker/plugins",
                    "ro": False
                }
        }

        # Assert
        m_os_path_exists.assert_called_once_with(log_dir)
        m_os_makedirs.assert_called_once_with(log_dir)
        m_check_system.assert_called_once_with(fix=False, quit_if_error=False)
        m_get_host_ips.assert_called_once_with(exclude=["docker0"])
        m_warn_if_unknown_ip.assert_called_once_with(ip_2, ip6)
        m_warn_if_hostname_conflict.assert_called_once_with(ip_2)
        m_install_kube.assert_called_once_with(node.KUBERNETES_PLUGIN_DIR)
        m_client.get_ip_pools.assert_has_calls([call(4), call(6)])
        m_client.ensure_global_config.assert_called_once_with()
        m_client.create_host.assert_called_once_with(
            node.hostname, ip_2, ip6, as_num
        )
        m_docker_client.remove_container.assert_called_once_with(
            'calico-node', force=True
        )

        getenv_calls = [call(ETCD_AUTHORITY_ENV, ETCD_AUTHORITY_DEFAULT),
                        call(node.POLICY_ONLY_ENV, "")]
        m_os_getenv.assert_has_calls(getenv_calls)

        m_docker.utils.create_host_config.assert_called_once_with(
            privileged=True,
            restart_policy={"Name":"Always"},
            network_mode="host",
            binds=binds
        )
        m_find_or_pull_node_image.assert_called_once_with(
            'node_image'
        )
        m_docker_client.create_container.assert_called_once_with(
            node_image,
            name='calico-node',
            detach=True,
            environment=environment,
            host_config='host_config',
            volumes=['/proc_host',
                     '/var/log/calico',
                     '/usr/share/docker/plugins']
        )
        m_docker_client.start.assert_called_once_with(container)
        m_attach_and_stream.assert_called_once_with(container)

    @patch('os.path.exists', autospec=True)
    @patch('os.makedirs', autospec=True)
    @patch('calico_ctl.node.check_system', autospec=True)
    @patch('calico_ctl.node.get_host_ips', autospec=True)
    @patch('calico_ctl.node.warn_if_unknown_ip', autospec=True)
    @patch('calico_ctl.node.warn_if_hostname_conflict', autospec=True)
    @patch('calico_ctl.node.install_kubernetes', autospec=True)
    def test_node_start_call_backup_kube_directory(
            self, m_install_kube, m_warn_if_hostname_conflict,
            m_warn_if_unknown_ip, m_get_host_ips, m_check_system,
            m_os_makedirs, m_os_path_exists):
        """
        Test that node_start calls the backup kuberentes plugin directory
        when install_kubernetes cannot access the default kubernetes directory
        """
        # Set up mock objects
        m_os_path_exists.return_value = True
        m_get_host_ips.return_value = ['1.1.1.1']
        m_install_kube.side_effect = OSError

        # Set up arguments
        node_image = 'node_image'
        log_dir = './log_dir'
        ip = ''
        ip6 = 'aa:bb::zz'
        as_num = ''
        detach = False
        kubernetes = True

        # Test expecting OSError exception
        self.assertRaises(OSError, node.node_start,
                          node_image, log_dir, ip, ip6, as_num, detach, kubernetes)
        m_install_kube.assert_has_calls([
            call(node.KUBERNETES_PLUGIN_DIR),
            call(node.KUBERNETES_PLUGIN_DIR_BACKUP)
        ])

    @patch('os.path.exists', autospec=True)
    @patch('os.makedirs', autospec=True)
    @patch('calico_ctl.node.check_system', autospec=True)
    @patch('calico_ctl.node.get_host_ips', autospec=True)
    @patch('calico_ctl.node.warn_if_unknown_ip', autospec=True)
    @patch('calico_ctl.node.warn_if_hostname_conflict', autospec=True)
    @patch('calico_ctl.node.install_kubernetes', autospec=True)
    @patch('calico_ctl.node.client', autospec=True)
    @patch('calico_ctl.node.docker_client', autospec=True)
    def test_node_start_remove_container_error(
            self, m_docker_client, m_client, m_install_kube,
            m_warn_if_hostname_conflict, m_warn_if_unknown_ip,
            m_get_host_ips, m_check_system, m_os_makedirs, m_os_path_exists):
        """
        Test that the docker client raises an APIError when it fails to
        remove a container.
        """
        # Set up mock objects
        err = APIError("Test error message", Response())
        m_docker_client.remove_container.side_effect = err

        # Set up arguments
        node_image = 'node_image'
        log_dir = './log_dir'
        ip = ''
        ip6 = 'aa:bb::zz'
        as_num = ''
        detach = False
        kubernetes = True

        # Testing expecting APIError exception
        self.assertRaises(APIError, node.node_start,
                          node_image, log_dir, ip, ip6, as_num, detach, kubernetes)

    @patch('sys.exit', autospec=True)
    @patch('os.path.exists', autospec=True)
    @patch('os.makedirs', autospec=True)
    @patch('calico_ctl.node.check_system', autospec=True)
    @patch('calico_ctl.node.get_host_ips', autospec=True)
    @patch('calico_ctl.node.warn_if_unknown_ip', autospec=True)
    @patch('calico_ctl.node.warn_if_hostname_conflict', autospec=True)
    @patch('calico_ctl.node.install_kubernetes', autospec=True)
    @patch('calico_ctl.node.client', autospec=True)
    @patch('calico_ctl.node.docker_client', autospec=True)
    def test_node_start_no_detected_ips(
            self, m_docker_client, m_client, m_install_kube,
            m_warn_if_hostname_conflict, m_warn_if_unknown_ip,
            m_get_host_ips, m_check_system, m_os_makedirs, m_os_path_exists,
            m_sys_exit):
        """
        Test that system exits when no ip is provided and host ips cannot be
        obtained
        """
        # Set up mock objects
        m_get_host_ips.return_value = []

        # Set up arguments
        node_image = 'node_image'
        log_dir = './log_dir'
        ip = ''
        ip6 = 'aa:bb::zz'
        as_num = ''
        detach = False
        kubernetes = True

        # Call method under test
        node.node_start(
            node_image, log_dir, ip, ip6, as_num, detach, kubernetes
        )

        # Assert
        m_sys_exit.assert_called_once_with(1)

    @patch('os.path.exists', autospec=True)
    @patch('os.makedirs', autospec=True)
    @patch('calico_ctl.node.check_system', autospec=True)
    @patch('calico_ctl.node.get_host_ips', autospec=True)
    @patch('calico_ctl.node.warn_if_unknown_ip', autospec=True)
    @patch('calico_ctl.node.warn_if_hostname_conflict', autospec=True)
    @patch('calico_ctl.node.install_kubernetes', autospec=True)
    @patch('calico_ctl.node.client', autospec=True)
    @patch('calico_ctl.node.docker_client', autospec=True)
    def test_node_start_create_default_ip_pools(
            self, m_docker_client, m_client, m_install_kube,
            m_warn_if_hostname_conflict, m_warn_if_unknown_ip,
            m_get_host_ips, m_check_system, m_os_makedirs, m_os_path_exists):
        """
        Test that the client creates default ipv4 and ipv6 pools when the
        client returns an empty ip_pool on etcd setup
        """
        # Set up mock objects
        m_client.get_ip_pools.return_value = []

        # Set up arguments
        node_image = 'node_image'
        log_dir = './log_dir'
        ip = ''
        ip6 = 'aa:bb::zz'
        as_num = ''
        detach = False
        kubernetes = True

        # Call method under test
        node.node_start(
            node_image, log_dir, ip, ip6, as_num, detach, kubernetes
        )

        # Assert
        m_client.add_ip_pool.assert_has_calls([
            call(4, node.DEFAULT_IPV4_POOL),
            call(6, node.DEFAULT_IPV6_POOL)
        ])

    @patch('calico_ctl.node.client', autospec=True)
    @patch('calico_ctl.node.docker_client', autospec=True)
    def test_node_stop(self, m_docker_client, m_client):
        """
        Test the client removes the host and stops the node when node_stop
        called
        """
        # Call method under test
        node.node_stop(True)

        # Assert
        m_client.remove_host.assert_called_once_with(node.hostname)
        m_docker_client.stop.assert_called_once_with('calico-node')

    @patch('calico_ctl.node.client', autospec=True)
    @patch('calico_ctl.node.docker_client', autospec=True)
    def test_node_stop_error(self, m_docker_client, m_client):
        """
        Test node_stop raises an exception when the docker client cannot not
        stop the node
        """
        # Set up mock objects
        err = APIError("Test error message", Response())
        m_docker_client.stop.side_effect = err

        # Call method under test expecting an exception
        self.assertRaises(APIError, node.node_stop, True)


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


    @parameterized.expand([
        ('1.2.3.4', False),
        ('abcde', False),
        ('aa:bb::cc:1234', False),
        ('aa::256', False),
        ('aa...bb:256', False),
        ('aa:256', True),
        ('1.2.3.244:256', True),
        ('1.2.a.244:256', True),
        ('-asr:100', False),
        ('asr-:100', False),
        ('asr-temp-test.thr.yes-33:100', True),
        ('asr-temp-test.-thr.yes-33:100', False),
        ('asr-temp-test.thr-.yes-33:100', False),
        ('asr-temp-test.thr-.yes-33:100', False),
        ('validhostname:0', False),
        ('validhostname:65536', False),
        ('validhostname:1', True),
        ('validhostname:65535', True),
        ('#notvalidhostname:65535', False),
        ('verylong' * 100 + ':200', False),
        ('12.256.122.43:aaa', False)
    ])
    def test_validate_hostname_port(self, input_string, expected_result):
        """
        Test validate_hostname_port function.

        This also tests validate_hostname which is invoked from
        validate_hostname_port.
        """
        test_result = validate_hostname_port(input_string)

        # Assert expected result
        self.assertEqual(expected_result, test_result)


class SysExitMock(Exception):
    """
    Used to mock the behaviour of sys.exit(), that is, ending execution of the
    code under test, without exiting the test framework.
    """
    pass
