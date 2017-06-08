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
import logging

from tests.st.test_base import TestBase
from tests.st.utils.docker_host import DockerHost

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


"""
Test calicoctl node version

Check that `calicoctl node run` runs the correct version of calico-node
(i.e. one which matches the version of calicoctl).
"""


class TestNodeVersion(TestBase):
    def test_node_version(self):
        """
        Check that `calicoctl node run` runs the correct version of calico-node
        (i.e. one which matches the version of calicoctl).
        """
        with DockerHost('host', dind=False, start_calico=True) as host:
            ctl_version_string = host.calicoctl("version | grep Version")
            node_version_string = host.execute(
                "docker ps --format '{{.Image}}' -f name=calico-node")
            logger.debug("ctl_version_string = %s", ctl_version_string)
            logger.debug("node_version_string = %s", node_version_string)
            ctl_version = ctl_version_string.split()[1]
            node_version = node_version_string.split(':')[1]
            assert (ctl_version == node_version), \
                "calicoctl version and calico/node version do not match!\n" \
                "ctl_version_string = %s, node_version_string = %s" % (ctl_version, node_version)
