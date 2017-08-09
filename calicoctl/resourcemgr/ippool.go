// Copyright (c) 2016 Tigera, Inc. All rights reserved.

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package resourcemgr

import (
	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/api/unversioned"
	"github.com/projectcalico/libcalico-go/lib/client"
)

func init() {
	registerResource(
		api.NewIPPool(),
		api.NewIPPoolList(),
		[]string{"CIDR"},
		[]string{"CIDR", "NAT", "IPIP"},
		map[string]string{
			"CIDR": "{{.Metadata.CIDR}}",
			"NAT":  "{{.Spec.NATOutgoing}}",
			"IPIP": "{{.Spec.IPIP.Mode}}",
		},
		func(client *client.Client, resource unversioned.Resource) (unversioned.Resource, error) {
			r := resource.(api.IPPool)
			return client.IPPools().Apply(&r)
		},
		func(client *client.Client, resource unversioned.Resource) (unversioned.Resource, error) {
			r := resource.(api.IPPool)
			return client.IPPools().Create(&r)
		},
		func(client *client.Client, resource unversioned.Resource) (unversioned.Resource, error) {
			r := resource.(api.IPPool)
			return client.IPPools().Update(&r)
		},
		func(client *client.Client, resource unversioned.Resource) (unversioned.Resource, error) {
			r := resource.(api.IPPool)
			return nil, client.IPPools().Delete(r.Metadata)
		},
		func(client *client.Client, resource unversioned.Resource) (unversioned.Resource, error) {
			r := resource.(api.IPPool)
			return client.IPPools().List(r.Metadata)
		},
	)
}
