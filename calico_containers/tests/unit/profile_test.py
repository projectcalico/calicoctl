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
from calico_ctl.profile import validate_arguments


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
