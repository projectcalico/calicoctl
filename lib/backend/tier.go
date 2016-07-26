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

package backend

import (
	"fmt"
	"regexp"

	"reflect"

	"github.com/golang/glog"
	"github.com/tigera/libcalico-go/lib/common"
)

var (
	matchTier = regexp.MustCompile("^/?calico/v1/policy/tier/([^/]+)/metadata$")
	typeTier  = reflect.TypeOf(Tier{})
)

type TierKey struct {
	Name string `json:"-" validate:"required,name"`
}

func (key TierKey) asEtcdKey() (string, error) {
	k, err := key.asEtcdDeleteKey()
	return k + "/metadata", err
}

func (key TierKey) asEtcdDeleteKey() (string, error) {
	if key.Name == "" {
		return "", common.ErrorInsufficientIdentifiers{Name: "name"}
	}
	e := fmt.Sprintf("/calico/v1/policy/tier/%s", key.Name)
	return e, nil
}

func (key TierKey) valueType() reflect.Type {
	return typeTier
}

func (key TierKey) String() string {
	return fmt.Sprintf("Tier(name=%s)", key.Name)
}

type TierListOptions struct {
	Name string
}

func (options TierListOptions) asEtcdKeyRoot() string {
	k := "/calico/v1/policy/tier"
	if options.Name == "" {
		return k
	}
	k = k + fmt.Sprintf("/%s/metadata", options.Name)
	return k
}

func (options TierListOptions) keyFromEtcdResult(ekey string) KeyInterface {
	glog.V(2).Infof("Get Tier key from %s", ekey)
	r := matchTier.FindAllStringSubmatch(ekey, -1)
	if len(r) != 1 {
		glog.V(2).Infof("Didn't match regex")
		return nil
	}
	name := r[0][1]
	if options.Name != "" && name != options.Name {
		glog.V(2).Infof("Didn't match name %s != %s", options.Name, name)
		return nil
	}
	return TierKey{Name: name}
}

type Tier struct {
	Order *float32 `json:"order,omitempty"`
}
