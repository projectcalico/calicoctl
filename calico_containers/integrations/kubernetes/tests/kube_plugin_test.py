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

import sys
if sys.version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins
import json
import unittest
import socket
from nose.tools import assert_equal, assert_true, assert_false
from mock import patch, Mock, MagicMock, mock_open
from subprocess import CalledProcessError
from calico_containers.integrations.kubernetes import calico_kubernetes
from pycalico.datastore import IF_PREFIX

class NetworkPluginTest(unittest.TestCase):

    def setUp(self):
        # Mock out sh when importing calico_kubernetes so it doesn't fail when
        # trying to find the calicoctl binary (which may not exist)
        with patch('calico_containers.integrations.'
                      'kubernetes.calico_kubernetes.sh') as m_sh:
            self.plugin = calico_kubernetes.NetworkPlugin()

    def test_create(self):
        with patch.object(self.plugin, '_configure_interface') as m_interface, \
                patch.object(self.plugin, '_configure_profile') as m_prof:
            # Set up mock objects
            m_interface.return_value = 'endpt_id'

            # Set up args
            args = ['script name','setup','','pod-name','dockerId']

            # Call method under test
            self.plugin.create(args)

            # Assert
            self.assertEqual('pod_name', self.plugin.pod_name)
            self.assertEqual('dockerId', self.plugin.docker_id)
            m_interface.assert_called_once_with()
            m_prof.assert_called_once_with('endpt_id')

    def test_create_fail(self):
        with patch.object(self.plugin, '_configure_interface') as m_interface, \
                patch.object(self.plugin, '_configure_profile') as m_prof, \
                patch('calico_containers.integrations.'
                      'kubernetes.calico_kubernetes.sys.exit') as m_sys:
            # Set up mock objects
            m_interface.side_effect = CalledProcessError(1,'','')

            # Set up args
            args = ['script name','setup','','podname','dockerId']

            # Call method under test
            self.plugin.create(args)

            # Assert
            m_sys.assert_called_once_with(1)

    def test_delete(self):
        with patch.object(self.plugin, 'calicoctl') as m_calicoctl:
            # Set up args
            args = ['script name','teardown', '','pod-name','dockerId']

            # Call method under test
            self.plugin.delete(args)

            # Assert
            self.assertEqual(self.plugin.pod_name, 'pod_name')
            self.assertEqual(self.plugin.docker_id, 'dockerId')
            m_calicoctl.assert_any_call('container', 'remove', 'dockerId')
            m_calicoctl.assert_any_call('profile', 'remove', 'pod_name')

    def test_configure_interface(self):
        with patch.object(self.plugin, '_read_docker_ip') as m_read_docker, \
                patch.object(self.plugin, '_delete_docker_interface') as m_delete_docker, \
                patch.object(calico_kubernetes, 'container_add') as m_add_container, \
                patch.object(calico_kubernetes, 'generate_cali_interface_name') as m_cali, \
                patch.object(self.plugin, '_get_node_ip') as m_node_ip, \
                patch.object(calico_kubernetes, 'check_call') as m_check_call:
            # Set up mock objects
            m_read_docker.return_value = 'docker_ip'
            class ep:
                endpoint_id = 'ep_id'
            m_add_container.return_value = ep
            m_cali.return_value = 'interface_name'
            m_node_ip.return_value = 'node_ip'

            # Call method under test
            return_val = self.plugin._configure_interface()

            # Assert
            m_read_docker.assert_called_once()
            m_delete_docker.assert_called_once()
            m_add_container.assert_called_once_with(
                self.plugin.docker_id, 'docker_ip', 'eth0')
            m_cali.assert_called_once_with(IF_PREFIX,'ep_id')
            m_node_ip.assert_called_once()
            m_check_call.assert_called_once_with(
                ['ip', 'addr', 'add', 'node_ip' + '/32',
                'dev', 'interface_name'])
            self.assertEqual(return_val.endpoint_id, 'ep_id')

    def test_get_node_ip(self):
        with patch('calico_containers.integrations.kubernetes.'
                    'calico_kubernetes.socket.socket') as m_socket:
            # Set up mock objects
            m_socket_return = MagicMock()
            m_socket_return.getsockname.return_value = ['ip_addr']
            m_socket.return_value = m_socket_return

            # Call method under test
            return_val = self.plugin._get_node_ip()

            # Assert
            m_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
            m_socket_return.connect.assert_called_once_with(('8.8.8.8', 80))
            m_socket_return.getsockname.assert_called_once_with()
            m_socket_return.close.assert_called_once_with()
            self.assertEqual(return_val, 'ip_addr')

    def test_read_docker_ip(self):
        with patch.object(calico_kubernetes,'check_output') as m_check_output:
            # Set up mock objects
            m_check_output.return_value = 'ip_addr'

            # Call method under test
            return_val = self.plugin._read_docker_ip()

            # Assert
            m_check_output.assert_called_once_with([
                'docker', 'inspect', '-format', '{{ .NetworkSettings.IPAddress }}',
                self.plugin.docker_id])
            self.assertEqual(return_val,'ip_addr')

    def test_delete_docker_interface(self):
        with patch.object(calico_kubernetes,'check_output') as m_check_output:
            # Set up mock objects
            m_check_output.return_value = 'pid'

            # Call method under test
            self.plugin._delete_docker_interface()

            # Assert
            m_check_output.assert_any_call([
                'docker', 'inspect', '-format', '{{ .State.Pid }}',
                self.plugin.docker_id])
            m_check_output.assert_any_call(
                ['mkdir', '-p', '/var/run/netns'])
            m_check_output.assert_any_call(
                ['ip', 'netns', 'exec', 'pid','ip', 'link', 'del', 'eth0'])
            m_check_output.assert_any_call(['rm', '/var/run/netns/pid'])

    def test_configure_profile(self):
        with patch.object(self.plugin, 'calicoctl') as m_calicoctl, \
                patch.object(self.plugin, '_get_pod_config') as m_pod_config, \
                patch.object(self.plugin, '_apply_rules') as m_rules, \
                patch.object(self.plugin, '_apply_tags') as m_tags:
            # Set up mock objects
            m_pod_config.return_value = 'pod'

            # Set up class members
            self.plugin.pod_name = 'podname'

            # Initialize args
            class endpoint:
                endpoint_id = 'ep_id'
            ep = endpoint

            # Call method under test
            self.plugin._configure_profile(ep)

            # Assert
            m_calicoctl.assert_any_call('profile','add','podname')
            m_pod_config.assert_called_once_with()
            m_rules.assert_called_once_with('podname', 'pod')
            m_tags.assert_called_once_with('podname', 'pod')
            m_calicoctl.assert_any_call('endpoint','ep_id','profile','set',self.plugin.pod_name)

    def test_get_pod_ports(self):
        # Initialize pod dictionary
        pod = {'spec':{'containers':[{'ports':[1,2,3]},{'ports':[4,5]}]}}
        ports = []

        # Append port numbers to a list for comparison
        for container in pod['spec']['containers']:
            ports.extend(container['ports'])

        # Call method under test
        return_val = self.plugin._get_pod_ports(pod)

        # Assert
        self.assertEqual(return_val,ports)

    def test_get_pod_ports_fail(self):
        # Initialize pod dictionary
        pod = {'spec':{'containers':[{'':[1,2,3]},{'':[4,5]}]}}
        ports = []

        # Call method under test
        return_val = self.plugin._get_pod_ports(pod)

        # Assert
        self.assertListEqual(return_val,ports)

    def test_get_pod_config(self):
        with patch.object(self.plugin, '_get_api_path') as m_api_path:
            # Set up mock object
            pod1 = {'metadata':{'name':'pod-1'}}
            pod2 = {'metadata':{'name':'pod-2'}}
            pod3 = {'metadata':{'name':'pod-3'}}
            pods = [pod1,pod2,pod3]
            m_api_path.return_value = pods

            # Set up class member
            self.plugin.pod_name = 'pod_2'

            # Call method under test
            return_val = self.plugin._get_pod_config()

            # Assert
            self.assertEqual(return_val,pod2)

    def test_get_pod_config_fail(self):
        with patch.object(self.plugin, '_get_api_path') as m_api_path:
            # Set up mock object and class members
            pod1 = {'metadata':{'name':'pod-1'}}
            pod2 = {'metadata':{'name':'pod-2'}}
            pod3 = {'metadata':{'name':'pod-3'}}
            pods = [pod1,pod2,pod3]
            m_api_path.return_value = pods

            # Set up class member
            self.plugin.pod_name = 'pod_4'

            # Call method under test expecting exception
            with self.assertRaises(KeyError):
                self.plugin._get_pod_config()


    def test_get_api_path(self):
        with patch.object(self.plugin, '_get_api_token') as m_api_token, \
                patch('calico_containers.integrations.kubernetes.'
                      'calico_kubernetes.requests.Session') as m_session, \
                patch.object(json, 'loads') as m_json_load:
            # Set up mock objects
            m_api_token.return_value = 'Token'
            m_session_return = Mock()
            m_session_return.headers = Mock()
            m_get_return = Mock()
            m_get_return.text = 'response_body'
            m_session_return.get.return_value = m_get_return
            m_session.return_value = m_session_return

            # Initialize args
            path = 'path'

            # Call method under test
            self.plugin._get_api_path(path)

            # Assert
            m_api_token.assert_called_once()
            m_session.assert_called_once_with()
            m_session_return.headers.update.assert_called_once_with(
                {'Authorization': 'Bearer ' + 'Token'})
            m_session_return.get.assert_called_once()
            m_json_load.assert_called_once_with('response_body')

    def test_get_api_token(self):
        with patch.object(builtins, 'open', mock_open(read_data='json_string')) as m_open, \
                patch.object(json,'loads') as m_json:
            # Set up mock objects
            m_json.return_value = {'BearerToken' : 'correct_return'}

            # Call method under test
            return_val = self.plugin._get_api_token()

            # Assert
            m_open.assert_called_once_with('/var/lib/kubelet/kubernetes_auth')
            m_json.assert_called_once_with('json_string')
            self.assertEqual(return_val,'correct_return')

    def test_generate_rules(self):
        # Call method under test
        return_val = self.plugin._generate_rules()

        # Assert
        self.assertEqual(return_val, ([{'action':'allow'}], [{'action' : 'allow'}]))

    def test_generate_profile_json(self):
        with patch('calico_containers.integrations.kubernetes.'
                   'calico_kubernetes.json.dumps') as m_json:
            # Set up mock objects
            m_json.return_value = 'correct_return'

            # Initialize args
            rules = ('inbound','outbound')
            profile_name = 'profile_name'

            # Call method under test
            return_val = self.plugin._generate_profile_json(
                profile_name,rules)

            # Assert
            m_json.assert_called_once_with(
                {'id': 'profile_name',
                'inbound_rules':'inbound',
                'outbound_rules':'outbound'},
                 indent=2)
            self.assertEqual(return_val,'correct_return')


    def test_apply_rules(self):
        with patch.object(self.plugin,'_generate_rules') as m_gen_rules, \
                patch.object(self.plugin,'_generate_profile_json') as m_prof_json, \
                patch.object(self.plugin,'calicoctl') as m_calicoctl:
            # Set up mock objects
            m_gen_rules.return_value = 'rules'
            m_prof_json.return_value = 'json_profile'
            profile = Mock()

            # Call method under test
            self.plugin._apply_rules(profile)

            # Assert
            m_gen_rules.assert_called_once_with()
            m_prof_json.assert_called_once_with(profile, 'rules')
            m_calicoctl.assert_called_once_with('profile',profile,'rule','update',_in='json_profile')

    def test_apply_tags(self):
        with patch.object(self.plugin, 'calicoctl') as m_calicoctl:
            # Intialize args
            pod = {'metadata':{'labels':{1:1,2:2}}}
            profile_name = 'profile_name'

            # Call method under test
            self.plugin._apply_tags(profile_name,pod)

            # Assert
            m_calicoctl.assert_any_call(
                'profile','profile_name','tag','add','1_1')
            m_calicoctl.assert_any_call(
                'profile','profile_name','tag','add','2_2')

    def test_apply_tags_fail(self):
        with patch.object(self.plugin, 'calicoctl') as m_calicoctl:
            # Intialize args
            pod = {}
            profile_name = 'profile_name'

            # Call method under test
            self.plugin._apply_tags(profile_name,pod)

            # Assert
            assert not m_calicoctl.called

if __name__ == '__main__':
    unittest.main()







