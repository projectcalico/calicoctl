// Copyright (c) 2017 Tigera, Inc. All rights reserved.

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

package commands_test

import (
	"github.com/projectcalico/calicoctl/calicoctl/commands"

	. "github.com/onsi/ginkgo"
	. "github.com/onsi/gomega"
	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/api/unversioned"
)

var _ = Describe("Test ValidateIDFieldsSame", func() {
	Context("with Profile Metadata", func() {
		var profile1 *api.Profile
		var profile2 *api.Profile
		BeforeEach(func() {
			profile1 = api.NewProfile()
			profile1.Metadata.Name = "testProfile1"
			profile2 = api.NewProfile()
			profile2.Metadata.Name = "testProfile1"
		})
		It("should not error out if the name is not changed", func() {
			before := []unversioned.ResourceObject{profile1}
			after := []unversioned.ResourceObject{profile2}
			err := commands.ValidateIDFieldsSame(before, after)
			Expect(err).NotTo(HaveOccurred())
		})
		It("should return an error if the name is changed", func() {
			profile2.Metadata.Name = "testName2"
			before := []unversioned.ResourceObject{profile1}
			after := []unversioned.ResourceObject{profile2}
			err := commands.ValidateIDFieldsSame(before, after)
			Expect(err).To(HaveOccurred())
		})
		It("should return an error if a resource is removed", func() {
			before := []unversioned.ResourceObject{profile1}
			after := []unversioned.ResourceObject{}
			err := commands.ValidateIDFieldsSame(before, after)
			Expect(err).To(HaveOccurred())
		})
		It("should return an error if a resource is added", func() {
			before := []unversioned.ResourceObject{}
			after := []unversioned.ResourceObject{profile2}
			err := commands.ValidateIDFieldsSame(before, after)
			Expect(err).To(HaveOccurred())
		})
	})
})
