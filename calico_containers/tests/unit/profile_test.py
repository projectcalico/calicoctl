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
from mock import patch
from nose_parameterized import parameterized
from calico_ctl.bgp import *
from calico_ctl.profile import validate_arguments, profile_rule_show,\
    profile_rule_update, profile_rule_add_remove


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
            validate_arguments(case)

            # Assert that method exits on bad input
            self.assertEqual(m_sys_exit.called, sys_exit_called)

    def test_profile_rule_show(self):
        """
        Test for profile_rule_show function
        """
        pass

    def test_profile_rule_update(self):
        """
        Test for profile_rule_update function
        """
        pass

    def test_profile_rule_add_remove(self):
        """
        Test for profile_rule_add_remove function
        """
        # Setup arguments to pass to method under test
        operation = 'add'
        name = 'profile1'
        position = None
        action = 'allow'
        direction = 'inbound'

        # Call method under test
        #profile_rule_add_remove(operation, name, position, action, direction)

    @parameterized.expand([('tcp') , ('udp')])
    def test_profile_rule_add_remove_tcp_udp_no_ports(self, protocol_arg):
        """
        Test for profile_rule_add_remove when protocol argument is specified
        with no src or dst ports indicated

        Assert that the system exits
        """
        # Setup arguments to pass to method under test
        operation = 'add'
        name = 'profile1'
        position = None
        action = 'allow'
        direction = 'inbound'
        protocol = protocol_arg

        # Call method under test
        self.assertRaises(SystemExit, profile_rule_add_remove,
                          operation, name, position, action, direction, protocol)


