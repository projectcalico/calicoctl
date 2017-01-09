// Copyright (c) 2016 Tigera, Inc. All rights reserved.
//
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
package autodetection

import (
	"errors"

	log "github.com/Sirupsen/logrus"
)

// FilteredEnumeration performs basic IP and IPNetwork discovery by enumerating
// all interfaces and filtering in/out based on the supplied filter regex.
func FilteredEnumeration(incl, excl []string, version int) (*Interface, *Addr, error) {
	interfaces, err := GetInterfaces(incl, excl, version)

	if err != nil {
		return nil, nil, err
	}
	if len(interfaces) == 0 {
		return nil, nil, errors.New("no valid interfaces found")
	}

	// Find the first interface with a valid IP address and network.
	// We initialise the IP with the first valid IP that we find just in
	// case we don't find an IP *and* network.
	var iface *Interface
	var addr *Addr
outer:
	for _, i := range interfaces {
		log.WithField("Name", i.Name).Info("Check interface")
		for _, a := range i.Addrs {
			log.WithField("Addr", a).Info("Check address")
			if !a.IPAddress.IsGlobalUnicast() {
				continue
			}

			// If the address has an IP and a Network then return
			// it.  Otherwise, if it just as an IP and we haven't
			// found one yet store this and return it if we don't
			// find one with a network.
			if a.IPNetwork != nil {
				iface = &i
				addr = &a
				break outer
			} else if addr == nil {
				iface = &i
				addr = &a
			}
		}
	}

	return iface, addr, nil
}
