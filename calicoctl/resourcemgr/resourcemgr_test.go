// Copyright (c) 2019 Tigera, Inc. All rights reserved.

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

package resourcemgr_test

import (
	"fmt"
	"io/ioutil"
	"os"

	"github.com/projectcalico/calicoctl/calicoctl/resourcemgr"
	api "github.com/projectcalico/libcalico-go/lib/apis/v3"
	"k8s.io/apimachinery/pkg/runtime"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
)

const (
	IppoolV6WithNeverVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 2002::/64
  ipipMode: Never
  vxlanMode: Never
  natOutgoing: true
`
	IppoolV6MissingVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 2002::/64
  ipipMode: Never
  natOutgoing: true
`
	IppoolV4WithAlwaysVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 192.168.0.0/16
  ipipMode: Never
  vxlanMode: Always
  natOutgoing: true
`
	IppoolV6WithAlwaysVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 2002::/64
  ipipMode: Never
  vxlanMode: Always
  natOutgoing: true
`
	IppoolV6WithErrorVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 2002::/64
  ipipMode: Never
  vxlanMode: NotDefined
  natOutgoing: true
`
	IppoolV6WithBothIPIPAndVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 2002::/64
  ipipMode: Always
  vxlanMode: Always
  natOutgoing: true
`
	IppoolV4WithBothIPIPAndVxlan = `kind: IPPool
apiVersion: projectcalico.org/v3
metadata:
  name: my-ippool
spec:
  cidr: 192.168.0.0/16
  ipipMode: Always
  vxlanMode: Always
  natOutgoing: true
`
)

var _ = Describe("Create resource from file", func() {
	It("Should create IPPOOL V6 with Vxlan to Never", func() {
		resources, err := createResources(IppoolV6WithNeverVxlan)
		Expect(err).NotTo(HaveOccurred())

		expectedIpPools := ipPpols(ipPool("2002::/64", api.VXLANModeNever, api.IPIPModeNever))

		expectResourcesToMatch(resources, expectedIpPools)
	})

	It("Should create IPPOOL V4 with Vxlan to Always", func() {
		resources, err := createResources(IppoolV4WithAlwaysVxlan)
		Expect(err).NotTo(HaveOccurred())

		expectedIpPools := ipPpols(ipPool("192.168.0.0/16", api.VXLANModeAlways, api.IPIPModeNever))

		expectResourcesToMatch(resources, expectedIpPools)
	})

	It("Should create IPPOOL V6 with missing Vxlan to Never", func() {
		resources, err := createResources(IppoolV6MissingVxlan)
		Expect(err).NotTo(HaveOccurred())

		expectedIpPools := ipPpols(ipPool("2002::/64", api.VXLANModeNever, api.IPIPModeNever))

		expectResourcesToMatch(resources, expectedIpPools)
	})

	It("Should not create IPPOOL V6 set to Always", func() {
		_, err := createResources(IppoolV6WithAlwaysVxlan)
		Expect(err).To(HaveOccurred())
	})

	It("Should not create IPPOOL V6 when Vxlan is not defined", func() {
		_, err := createResources(IppoolV6WithErrorVxlan)
		Expect(err).To(HaveOccurred())
	})

	It("Should not create IPPOOL V6 when Vxlan and IpIp are both defined", func() {
		_, err := createResources(IppoolV6WithBothIPIPAndVxlan)
		Expect(err).To(HaveOccurred())
	})

	It("Should not create IPPOOL V4 when Vxlan and IpIp are both defined", func() {
		_, err := createResources(IppoolV4WithBothIPIPAndVxlan)
		Expect(err).To(HaveOccurred())
	})
})

func expectResourcesToMatch(resources []runtime.Object, expectedIpPools []*api.IPPool) {
	Expect(len(expectedIpPools)).To(Equal(len(resources)))
	for index := range expectedIpPools {
		Expect(resources[index].DeepCopyObject()).To(Equal(expectedIpPools[index]))
	}
}

func ipPool(cidr string, vxlanMode api.VXLANMode, ipipMode api.IPIPMode) *api.IPPool {
	ippool := api.NewIPPool()
	ippool.Name = "my-ippool"
	ippool.Spec = api.IPPoolSpec{CIDR: cidr, VXLANMode: vxlanMode, IPIPMode: ipipMode, NATOutgoing: true}
	return ippool
}

func ipPpols(elements ...*api.IPPool) []*api.IPPool {
	return elements
}

func createResources(spec string) ([]runtime.Object, error) {
	By("Writing the spec to a temporary location")
	file := writeSpec(spec)
	defer os.Remove(file.Name())
	By(fmt.Sprintf("Creating resources from file %s", file.Name()))
	return resourcemgr.CreateResourcesFromFile(file.Name())
}

func writeSpec(spec string) *os.File {
	file, err := ioutil.TempFile("/tmp", "resource")
	file.WriteString(spec)
	Expect(err).NotTo(HaveOccurred())
	return file
}
