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
from mock import patch, Mock, call, mock_open
from netaddr import IPAddress
from sh import Command, CommandNotFound
from tarfile import TarFile
from calico_ctl.bgp import *
from calico_ctl.bgp import validate_arguments as bgp_validate_arguments
from calico_ctl import diags
from calico_ctl.endpoint import validate_arguments as ep_validate_arguments
from calico_ctl.node import validate_arguments as node_validate_arguments
from calico_ctl.pool import validate_arguments as pool_validate_arguments
from calico_ctl.profile import validate_arguments as profile_validate_arguments
from calico_ctl.container import validate_arguments as container_validate_arguments
from pycalico.datastore_datatypes import BGPPeer
from pycalico.datastore import DatastoreClient
from etcd import EtcdResult, EtcdException, Client


class TestBgp(unittest.TestCase):

    @patch('sys.exit', autospec=True)
    def test_validate_arguments(self, m_sys_exit):
        """
        Test validate_arguments for calicoctl bgp command
        """
        # Set up arguments
        cases = (
            ({'<PEER_IP>':'127.a.0.1'}, False),
            ({'<PEER_IP>':'aa:bb::zz'}, False),
            ({'<AS_NUM>':9}, True),
            ({'<AS_NUM>':'9'}, True),
            ({'<AS_NUM>':'nine'}, False),
            ({'show':1, '--ipv4':1}, True)
        )

        # Call method under test for each test case
        # Assert that method exits on bad input
        for case, is_valid in cases:
            print "Testing case %s ..." % case
            bgp_validate_arguments(case)
            if is_valid:
                assert not m_sys_exit.called
            else:
                assert m_sys_exit.called
            m_sys_exit.reset_mock()

    @patch('calico_ctl.bgp.check_ip_version', autospec=True)
    @patch('calico_ctl.bgp.BGPPeer', autospec=True)
    @patch('calico_ctl.bgp.client', autospec=True)
    def test_bgp_peer_add(self, m_client, m_BGPPeer, m_check_ipv):
        """
        Test bgp_peer_add function for calico_ctl bgp
        """
        # Set up mock objects
        address = '1.2.3.4'
        peer = Mock(spec=BGPPeer)
        m_check_ipv.return_value = address
        m_BGPPeer.return_value = peer

        # Call method under test
        bgp_peer_add('1.2.3.4', 'v4', 1)

        # Assert
        m_check_ipv.assert_called_once_with('1.2.3.4', 'v4', IPAddress)
        m_BGPPeer.assert_called_once_with(address, 1)
        m_client.add_bgp_peer.assert_called_once_with('v4', peer)

    @patch('calico_ctl.bgp.check_ip_version', autospec=True)
    @patch('calico_ctl.bgp.client', autospec=True)
    def test_bgp_peer_remove(self, m_client, m_check_ipv):
        """
        Test bgp_peer_remove function for calicoctl bgp
        """
        # Set up mock objects
        address = '1.2.3.4'
        m_check_ipv.return_value = address

        # Call method under test
        bgp_peer_remove('1.2.3.0', 'v4')

        # Assert
        m_check_ipv.assert_called_once_with('1.2.3.0', 'v4', IPAddress)
        m_client.remove_bgp_peer.assert_called_once_with('v4', address)

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

    @patch('sys.exit', autospec=True)
    def test_validate_arguments(self, m_sys_exit):
        """
        Test validate_arguments for calicoctl container command
        """
        # Set up arguments
        cases =(
            ({'<CONTAINER>':'node1', 'ip':1, 'add':1, '<IP>':'127.a.0.1'}, False),
            ({'<CONTAINER>':'node1', 'ip':1, 'add':1, '<IP>':'aa:bb::zz'}, False),
            ({'add':1, '<CONTAINER>':'node1', '<IP>':'127.a.0.1'}, False),
            ({'add':1, '<CONTAINER>':'node1', '<IP>':'aa:bb::zz'}, False)
        )

        # Call method under test for each test case
        # Assert that method exits on bad input
        for case, is_valid in cases:
            print "Testing case %s ..." % case
            container_validate_arguments(case)
            if is_valid:
                assert not m_sys_exit.called
            else:
                assert m_sys_exit.called
            m_sys_exit.reset_mock()


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
    def test_save_diags(self, m_upload_temp_diags, m_DatastoreClient,
                        m_tarfile_open, m_copytree, m_sh_command, m_socket,
                        m_open, m_datetime, os_path_isdir, m_os_mkdir, m_tempfile):
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
        m_copytree.assert_called_once_with(log_dir, diags_dir + '/logs')
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
    def test_save_diags_exceptions(
            self, m_DatastoreClient, m_tarfile_open, m_copytree, m_sh_command,
            m_socket, m_open, m_datetime, m_os_path_isdir, m_os_mkdir, m_tempfile):
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

    @patch('sys.exit', autospec=True)
    def test_validate_arguments(self, m_sys_exit):
        """
        Test validate_arguments for calicoctl endpoint command
        """
        # Set up arguments
        cases = (
            ({'<PROFILES>':['profile-1', 'profile-2', 'profile-3']}, True),
            ({'<PROFILES>':['Profile1', 'Profile!']}, False),
            ({}, True)
        )

        # Call method under test
        for case, is_valid in cases:
            ep_validate_arguments(case)
            if is_valid:
                assert not m_sys_exit.called
            else:
                assert m_sys_exit.called
            m_sys_exit.reset_mock()


class TestNode(unittest.TestCase):

    @patch('sys.exit', autospec=True)
    def test_validate_arguments(self, m_sys_exit):
        """
        Test validate_arguments for calicoctl node command
        """
        # Set up arguments
        cases = (
            ({'--ip':'127.a.0.1'}, False),
            ({'--ip':'aa:bb::cc'}, False),
            ({'--ip':'127.0.0.1', '--ip6':'127.0.0.1'}, False),
            ({'--ip':'127.0.0.1', '--ip6':'aa:bb::zz'}, False)
        )

        # Call method under test for each test case
        # Assert that method exits on bad input
        for case, is_valid in cases:
            print "Testing case %s ..." % case
            node_validate_arguments(case)
            if is_valid:
                assert not m_sys_exit.called
            else:
                assert m_sys_exit.called
            m_sys_exit.reset_mock()


class TestPool(unittest.TestCase):

    @patch('sys.exit', autospec=True)
    def test_validate_arguments(self, m_sys_exit):
        """
        Test validate_arguments for calicoctl pool command
        """
        # Set up arguments
        cases = (
            ({'add':1, '<CIDR>':'127.a.0.1'}, False),
            ({'add':1, '<CIDR>':'aa:bb::zz'}, False),
            ({'add':1, '<CIDR>':'1.2.3.4'}, True),
            ({'add':1, '<CIDR>':'1.2.3.0/24'}, True),
            ({'add':1, '<CIDR>':'aa:bb::ff'}, True)
        )

        # Call method under test for each test case
        # Assert that method exits on bad input
        for case, is_valid in cases:
            print "Testing case %s ..." % case
            pool_validate_arguments(case)
            if is_valid:
                assert not m_sys_exit.called
            else:
                assert m_sys_exit.called
            m_sys_exit.reset_mock()


class TestProfile(unittest.TestCase):

    @patch('sys.exit', autospec=True)
    def test_validate_arguments(self, m_sys_exit):
        """
        Test validate_arguments for calicoctl profile command
        """
        # Set up arguments
        cases = (
            ({'<PROFILE>':'profile-1'}, True),
            ({'<PROFILE>':'Profile!'}, False),
            ({'<SRCTAG>':'Tag-1', '<DSTTAG>':'Tag-2'}, True),
            ({'<SRCTAG>':'Tag~1', '<DSTTAG>':'Tag~2'}, False),
            ({'<SRCCIDR>':'127.a.0.1'}, False),
            ({'<DSTCIDR>':'aa:bb::zz'}, False),
            ({'<SRCCIDR>':'1.2.3.4', '<DSTCIDR>':'1.2.3.4'}, True),
            ({'<ICMPCODE>':'5'}, True),
            ({'<ICMPTYPE>':'16'}, True),
            ({'<ICMPCODE>':100, '<ICMPTYPE>':100}, True),
            ({'<ICMPCODE>':4, '<ICMPTYPE>':255}, False),
            ({}, True)
        )

        # Call method under test for each test case
        # Assert that method exits on bad input
        for case, is_valid in cases:
            print "Testing case %s ..." % case
            profile_validate_arguments(case)
            if is_valid:
                assert not m_sys_exit.called
            else:
                assert m_sys_exit.called
            m_sys_exit.reset_mock()
