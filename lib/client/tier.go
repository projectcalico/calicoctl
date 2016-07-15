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

package client

import (
	"github.com/tigera/libcalico-go/lib/api"
	"github.com/tigera/libcalico-go/lib/backend"
)

// TierInterface has methods to work with Tier resources.
type TierInterface interface {
	List(api.TierMetadata) (*api.TierList, error)
	Get(api.TierMetadata) (*api.Tier, error)
	Create(*api.Tier) (*api.Tier, error)
	Update(*api.Tier) (*api.Tier, error)
	Apply(*api.Tier) (*api.Tier, error)
	Delete(api.TierMetadata) error
}

// tiers implements TierInterface
type tiers struct {
	c *Client
}

// newTiers returns a tiers
func newTiers(c *Client) *tiers {
	return &tiers{c}
}

// List takes a Metadata, and returns the list of tiers that match that Metadata
// (wildcarding missing fields)
func (h *tiers) List(metadata api.TierMetadata) (*api.TierList, error) {
	if l, err := h.c.list(backend.Tier{}, metadata, h, nil); err != nil {
		return nil, err
	} else {
		hl := api.NewTierList()
		hl.Items = make([]api.Tier, 0, len(l))
		for _, h := range l {
			hl.Items = append(hl.Items, *h.(*api.Tier))
		}
		return hl, nil
	}
}

// Get returns information about a particular tier.
func (h *tiers) Get(metadata api.TierMetadata) (*api.Tier, error) {
	if a, err := h.c.get(backend.Tier{}, metadata, h, nil); err != nil {
		return nil, err
	} else {
		h := a.(*api.Tier)
		return h, nil
	}
}

// Create creates a new tier.
func (h *tiers) Create(a *api.Tier) (*api.Tier, error) {
	return a, h.c.create(*a, h, nil)
}

// Create creates a new tier.
func (h *tiers) Update(a *api.Tier) (*api.Tier, error) {
	return a, h.c.update(*a, h, nil)
}

// Create creates a new tier.
func (h *tiers) Apply(a *api.Tier) (*api.Tier, error) {
	return a, h.c.apply(*a, h, nil)
}

// Delete deletes an existing tier.
func (h *tiers) Delete(metadata api.TierMetadata) error {
	return h.c.delete(metadata, h)
}

// Convert a TierMetadata to a TierListInterface
func (h *tiers) convertMetadataToListInterface(m interface{}) (backend.ListInterface, error) {
	hm := m.(api.TierMetadata)
	l := backend.TierListOptions{
		Name: hm.Name,
	}
	return l, nil
}

// Convert a TierMetadata to a TierKeyInterface
func (h *tiers) convertMetadataToKeyInterface(m interface{}) (backend.KeyInterface, error) {
	hm := m.(api.TierMetadata)
	k := backend.TierKey{
		Name: hm.Name,
	}
	return k, nil
}

// Convert an API Tier structure to a Backend Tier structure
func (h *tiers) convertAPIToBackend(a interface{}) (interface{}, error) {
	at := a.(api.Tier)
	k, err := h.convertMetadataToKeyInterface(at.Metadata)
	if err != nil {
		return nil, err
	}
	tk := k.(backend.TierKey)

	bt := backend.Tier{
		TierKey: tk,

		Order: at.Spec.Order,
	}

	return bt, nil
}

// Convert a Backend Tier structure to an API Tier structure
func (h *tiers) convertBackendToAPI(b interface{}) (interface{}, error) {
	bt := *b.(*backend.Tier)
	at := api.NewTier()

	at.Metadata.Name = bt.Name

	at.Spec.Order = bt.Order

	return at, nil
}

func (h *tiers) copyKeyValues(kvs []backend.KeyValue, b interface{}) {
	bp := b.(*backend.Tier)
	k := kvs[0].Key.(backend.TierKey)
	bp.TierKey = k
}
