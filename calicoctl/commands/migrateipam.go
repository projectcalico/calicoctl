// Copyright (c) 2020 Tigera, Inc. All rights reserved.

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

package commands

import (
	"context"
	"fmt"
	"time"

	bapi "github.com/projectcalico/libcalico-go/lib/backend/api"
	"github.com/projectcalico/libcalico-go/lib/backend/model"
	client "github.com/projectcalico/libcalico-go/lib/clientv3"
	"github.com/projectcalico/libcalico-go/lib/errors"
	"github.com/projectcalico/libcalico-go/lib/net"
)

type migrateIPAM struct {
	client          bapi.Client
	BlockAffinities []*BlockAffinityKVPair `json:"block_affinities,omitempty"`
	IPAMBlocks      []*IPAMBlockKVPair     `json:"blocks,omitempty"`
	IPAMHandles     []*IPAMHandleKVPair    `json:"handles,omitempty"`
	IPAMConfig      *IPAMConfigKVPair      `json:"config,omitempty"`
}

type BlockAffinityKVPair struct {
	Key      *BlockAffinityKey
	Value    *model.BlockAffinity
	Revision string
	TTL      time.Duration // For writes, if non-zero, key has a TTL.
}

type BlockAffinityKey struct {
	CIDR net.IPNet `json:"cidr,omitempty"`
	Host string    `json:"host,omitempty"`
}

type IPAMBlockKVPair struct {
	Key      *BlockKey
	Value    *model.AllocationBlock
	Revision string
	TTL      time.Duration // For writes, if non-zero, key has a TTL.
}

type BlockKey struct {
	CIDR net.IPNet `json:"cidr,omitempty"`
}

type IPAMHandleKVPair struct {
	Key      *model.IPAMHandleKey
	Value    *model.IPAMHandle
	Revision string
	TTL      time.Duration // For writes, if non-zero, key has a TTL.
}

type IPAMConfigKVPair struct {
	Key      *model.IPAMConfigKey
	Value    *model.IPAMConfig
	Revision string
	TTL      time.Duration // For writes, if non-zero, key has a TTL.
}

// ipamResults contains the results from executing an IPAM backend command
// TODO: May not need this if we decide not to print out the resources that were imported
type ipamResults struct {
	// The number of resources that are being configured.
	numResources int

	// The number of resources that were actually configured.  This will
	// never be 0 without an associated error.
	numHandled int

	// The results returned from each invocation
	resources []*model.KVPair

	// Errors associated with individual resources
	resErrs []error
}

func NewMigrateIPAM(c client.Interface) *migrateIPAM {
	type accessor interface {
		Backend() bapi.Client
	}
	bc := c.(accessor).Backend()
	return &migrateIPAM{
		client: bc,
	}
}

func (m *migrateIPAM) PullFromDatastore() error {
	ctx := context.Background()

	blockKVList, err := m.client.List(ctx, model.BlockListOptions{}, "")
	if err != nil {
		return err
	}

	blockAffinityKVList, err := m.client.List(ctx, model.BlockAffinityListOptions{}, "")
	if err != nil {
		return err
	}

	ipamHandleKVList, err := m.client.List(ctx, model.IPAMHandleListOptions{}, "")
	if err != nil {
		return err
	}

	ipamConfigKV, err := m.client.Get(ctx, model.IPAMConfigKey{}, "")
	if err != nil {
		// If the resource does not exist, do not throw the error
		if _, ok := err.(errors.ErrorResourceDoesNotExist); !ok {
			return err
		}
	}

	// Convert all of the abstract KV Pairs into the appropriate types.
	blocks := []*IPAMBlockKVPair{}
	for _, item := range blockKVList.KVPairs {
		modelBlockKey, ok := item.Key.(model.BlockKey)
		if !ok {
			return fmt.Errorf("Could not convert %+v to a BlockKey", item.Key)
		}

		// Convert this to a key that has values for json encoding.
		blockKey := BlockKey{
			CIDR: modelBlockKey.CIDR,
		}

		block, ok := item.Value.(*model.AllocationBlock)
		if !ok {
			return fmt.Errorf("Could not convert %+v to an AllocationBlock", item.Value)
		}
		blocks = append(blocks, &IPAMBlockKVPair{
			Key:      &blockKey,
			Value:    block,
			Revision: item.Revision,
			TTL:      item.TTL,
		})
	}

	blockAffinities := []*BlockAffinityKVPair{}
	for _, item := range blockAffinityKVList.KVPairs {
		modelBlockAffinityKey, ok := item.Key.(model.BlockAffinityKey)
		if !ok {
			return fmt.Errorf("Could not convert %+v to a BlockAffinityKey", item.Key)
		}

		// Convert this to a key that has vlaues for json encoding.
		blockAffinityKey := BlockAffinityKey{
			CIDR: modelBlockAffinityKey.CIDR,
			Host: modelBlockAffinityKey.Host,
		}

		blockAffinity, ok := item.Value.(*model.BlockAffinity)
		if !ok {
			return fmt.Errorf("Could not convert %+v to a BlockAffinity", item.Value)
		}
		blockAffinities = append(blockAffinities, &BlockAffinityKVPair{
			Key:      &blockAffinityKey,
			Value:    blockAffinity,
			Revision: item.Revision,
			TTL:      item.TTL,
		})
	}

	ipamHandles := []*IPAMHandleKVPair{}
	for _, item := range ipamHandleKVList.KVPairs {
		handleKey, ok := item.Key.(model.IPAMHandleKey)
		if !ok {
			return fmt.Errorf("Could not convert %+v to an IPAMHandleKey", item.Key)
		}
		handle, ok := item.Value.(*model.IPAMHandle)
		if !ok {
			return fmt.Errorf("Could not convert %+v to an IPAMHandle", item.Value)
		}
		ipamHandles = append(ipamHandles, &IPAMHandleKVPair{
			Key:      &handleKey,
			Value:    handle,
			Revision: item.Revision,
			TTL:      item.TTL,
		})
	}

	var ipamConfig *IPAMConfigKVPair
	if ipamConfigKV != nil {
		configKey, ok := ipamConfigKV.Key.(model.IPAMConfigKey)
		if !ok {
			return fmt.Errorf("Could not convert %+v to an IPAMConfigKey", ipamConfigKV.Key)
		}
		config, ok := ipamConfigKV.Value.(*model.IPAMConfig)
		if !ok {
			return fmt.Errorf("Could not convert %+v to an IPAMConfig", ipamConfigKV.Value)
		}
		ipamConfig = &IPAMConfigKVPair{
			Key:      &configKey,
			Value:    config,
			Revision: ipamConfigKV.Revision,
			TTL:      ipamConfigKV.TTL,
		}
	}

	// Store the information
	m.BlockAffinities = blockAffinities
	m.IPAMBlocks = blocks
	m.IPAMHandles = ipamHandles
	m.IPAMConfig = ipamConfig
	return nil
}

// TODO: Cannot use the backend client for this. Need a better way
func (m *migrateIPAM) PushToDatastore() ipamResults {
	ctx := context.Background()
	errs := []error{}
	handled := 0
	resources := []*model.KVPair{}

	for _, bakv := range m.BlockAffinities {
		kv := &model.KVPair{
			Key: model.BlockAffinityKey{
				CIDR: bakv.Key.CIDR,
				Host: bakv.Key.Host,
			},
			Value:    bakv.Value,
			Revision: bakv.Revision,
			TTL:      bakv.TTL,
		}
		created, err := m.client.Create(ctx, kv)
		if err != nil {
			errs = append(errs, fmt.Errorf("Error trying to create block affinity %s: %s", kv.Key.String(), err))
		}
		resources = append(resources, created)
		handled++
	}

	for _, bkv := range m.IPAMBlocks {
		kv := &model.KVPair{
			Key: model.BlockKey{
				CIDR: bkv.Key.CIDR,
			},
			Value:    bkv.Value,
			Revision: bkv.Revision,
			TTL:      bkv.TTL,
		}
		created, err := m.client.Create(ctx, kv)
		if err != nil {
			errs = append(errs, fmt.Errorf("Error trying to create block affinity %s: %s", kv.Key.String(), err))
		}
		resources = append(resources, created)
		handled++
	}

	for _, hkv := range m.IPAMHandles {
		kv := &model.KVPair{
			Key:      *hkv.Key,
			Value:    hkv.Value,
			Revision: hkv.Revision,
			TTL:      hkv.TTL,
		}
		created, err := m.client.Create(ctx, kv)
		if err != nil {
			errs = append(errs, fmt.Errorf("Error trying to create block affinity %s: %s", kv.Key.String(), err))
		}
		resources = append(resources, created)
		handled++
	}

	ipamConfigCount := 0
	if m.IPAMConfig != nil {
		ipamConfigCount = 1
		kv := &model.KVPair{
			Key:      *m.IPAMConfig.Key,
			Value:    m.IPAMConfig.Value,
			Revision: m.IPAMConfig.Revision,
			TTL:      m.IPAMConfig.TTL,
		}
		created, err := m.client.Create(ctx, kv)
		if err != nil {
			errs = append(errs, fmt.Errorf("Error trying to create block affinity %s: %s", kv.Key.String(), err))
		}
		resources = append(resources, created)
		handled++
	}

	return ipamResults{
		numResources: len(m.BlockAffinities) + len(m.IPAMBlocks) + len(m.IPAMHandles) + ipamConfigCount,
		numHandled:   handled,
		resources:    resources,
		resErrs:      errs,
	}
}
