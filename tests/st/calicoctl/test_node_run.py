# Copyright (c) 2015-2017 Tigera, Inc. All rights reserved.
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
from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
import time

from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost
from tests.st.utils.exceptions import CommandExecError
from tests.st.utils.utils import retry_until_success
import os

"""
Test calicoctl node run

The `calicoctl node run` command is tested fairly throughouly by other tests.  Here we
want to test passing env vars through `calicoctl node run` into the container.
"""

class TestNodeRun(TestBase):
    def test_node_run_dryrun(self):
        """
        Test that dryrun does not output ETCD_AUTHORITY or ETCD_SCHEME.
        """
        with DockerHost('host', dind=False, start_calico=False) as host:
            output = host.calicoctl("node run --dryrun")
            assert "ETCD_AUTHORITY" not in output
            assert "ETCD_SCHEME" not in output
            assert "ETCD_ENDPOINTS" in output


class TestNodeRun(TestBase):
    
    def test_node_run_passes_env_vars(self):
        """
        Set some CALICO_ and FELIX_ env vars and see that they make it through to the
        Node container
        """
        env_vars = {'CALICO_TESTVAL': 'dummyVal',
                    'FELIX_TESTVAL': 'felixDummyVal'}

        with DockerHost('host', dind=False, start_calico=True,
                        calico_env_vars=env_vars) as host:
            calico_out = host.execute('docker exec -ti calico-node printenv CALICO_TESTVAL')
            felix_out = host.execute('docker exec -ti calico-node printenv FELIX_TESTVAL')

            self.assertEquals(calico_out, 'dummyVal')
            self.assertEquals(felix_out, 'felixDummyVal')

            # Veryify calico-node started with dummy values
            logs = host.execute('docker logs calico-node')
            self.assertIn('Calico node started successfully', logs)

    def test_env_vars_are_used(self):
        """
        Test that CALICO_ env vars are used when set
        """
        env_vars = {'CALICO_NETWORKING_BACKEND': 'none',
                    'FELIX_LOGSEVERITYSCREEN': 'DEBUG'}

        with DockerHost('host', dind=False, start_calico=True,
                        calico_env_vars=env_vars) as host:
            logs = host.execute('docker logs calico-node | grep -i CALICO_NETWORKING_BACKEND')

            self.assertIn(
                'CALICO_NETWORKING_BACKEND is none - no BGP daemon running',
                logs)

            def check_logs():
                felix_logs = host.execute(
                    'docker exec -it calico-node cat /var/log/calico/felix/current | grep -i LOGSEVERITYSCREEN')
                self.assertIn('Parsed value for LogSeverityScreen: DEBUG (from environment variable)',
                              felix_logs)
            retry_until_success(check_logs, 10)
