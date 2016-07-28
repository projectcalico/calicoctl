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
	"reflect"

	"github.com/tigera/libcalico-go/lib/api"
)

// Key represents a parsed datastore key.
type Key interface {
	// defaultPath() returns a default stringified path for this object,
	// suitable for use in most datastores (and used on the Felix API,
	// for example).
	defaultPath() (string, error)
	// defaultDeletePath() returns a default stringified path for deleting
	// this object.
	defaultDeletePath() (string, error)
	valueType() reflect.Type
}

// Interface used to perform datastore lookups.
type ListInterface interface {
	// defaultPathRoot() returns a default stringified root path, i.e. path
	// to the directory containing all the keys to be listed.
	defaultPathRoot() string
	keyFromEtcdResult(key string) Key
}

// KVPair holds a parsed key and value as well as datastore specific revision
// information.
type KVPair struct {
	Key      Key
	Value    interface{}
	Revision interface{}
}

// Client is the interface that a backend datastore must implement.
type Client interface {
	Create(object *KVPair) (*KVPair, error)
	Update(object *KVPair) (*KVPair, error)
	Apply(object *KVPair) (*KVPair, error)
	Delete(object *KVPair) error
	Get(key Key) (*KVPair, error)
	List(list ListInterface) ([]*KVPair, error)
}

// NewClient creates a new backend datastore client.
func NewClient(config *api.ClientConfig) (c Client, err error) {
	// Currently backend client is only supported by etcd.
	c, err = ConnectEtcdClient(config)
	return
}
