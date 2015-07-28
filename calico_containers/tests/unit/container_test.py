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
from mock import patch, Mock, call
from nose_parameterized import parameterized
from calico_ctl.container import validate_arguments as container_validate_arguments
from calico_ctl.container import container_add


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

    @patch("calico_ctl.container.get_container_info_or_exit", autospec=True)
    @patch("calico_ctl.container.enforce_root", autospec=True)
    @patch("calico_ctl.container.sys", autospec=True)
    @patch("calico_ctl.container.client", autospec=True)
    def test_container_add_host_network(self, m_client, m_sys,m_root, m_info):
        """
        Test container_add exits if the container has host networking.
        """

        info = {"Id": "TEST_ID",
                "State": {"Running": True},
                "HostConfig": {"NetworkMode": "host"}}
        m_info.return_value = info
        m_client.get_endpoint.side_effect = KeyError()
        m_sys.exit.side_effect = SysExitMock()

        # Run function under test.
        name = "TEST_NAME"
        ip = "10.1.2.3"
        interface = "eth1"
        self.assertRaises(SysExitMock, container_add, name, ip, interface)

        m_root.assert_called_once_with()
        m_info.assert_called_once_with(name)
        m_sys.exit.assert_called_once_with(1)


class SysExitMock(Exception):
    """
    Used to mock the behaviour of sys.exit(), that is, ending execution of the
    code under test, without exiting the test framework.
    """
    pass
