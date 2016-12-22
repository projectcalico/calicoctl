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
package main

import (
	"encoding/hex"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/satori/go.uuid"

	"strings"

	log "github.com/Sirupsen/logrus"
	"github.com/projectcalico/calico-containers/calico_node/autodetection"
	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/backend/model"
	bapi "github.com/projectcalico/libcalico-go/lib/backend/model"
	"github.com/projectcalico/libcalico-go/lib/client"
	"github.com/projectcalico/libcalico-go/lib/errors"
	cnet "github.com/projectcalico/libcalico-go/lib/net"
	"github.com/projectcalico/libcalico-go/lib/numorstring"
)

// main performs startup operations for a node.
// For now, this only creates the ClusterGUID.  Ultimately,
// all of the function from startup.py will be moved here.

func main() {
	// Build a Calico client.
	log.Info("Creating Calico client")
	cfg, err := client.LoadClientConfig("")
	if err != nil {
		panic(fmt.Sprintf("Error loading config: %s", err))
	}
	c, err := client.New(*cfg)
	if err != nil {
		panic(fmt.Sprintf("Error creating client: %s", err))
	}

	nodeName := os.Getenv("NODENAME")
	if nodeName == "" {
		nodeName = os.Getenv("HOSTNAME")
	}
	if nodeName == "" {
		nodeName, err := os.Hostname()
		if err != nil {
			log.Warnf("Failed to get hostname: %s", err)
		}
	}

	meta := api.NodeMetadata{Name: nodeName}
	waitForDatastore()
	log.Info("Connected to datastore")

	log.Info("Ensuring datastore is initialized")
	err = c.EnsureInitialized()
	if err != nil {
		log.Warnf("Error initializing datastore: %s", err)
		panic(err)
	}
	log.Info("Datastore is initialized")

	// Make sure we have a global cluster ID set.
	log.Info("Ensuring a cluster guid is set")
	ensureClusterGUID(c)

	if d := os.Getenv("DATASTORE_TYPE"); d == "kubernetes" {
		f, err := os.OpenFile("startup.env", os.O_APPEND|os.O_WRONLY, 0600)
		if err != nil {
			panic(fmt.Sprintf("Error loading config: %s", err))
		}
		f.WriteString("export DATASTORE_TYPE=kubernetes\n")
		f.WriteString("export HOSTNAME=" + nodeName + "\n")
	}

	ip := os.Getenv("IP")
	if ip != "" {
		if validIP := net.ParseIP(ip); validIP.To4() == nil {
			ip = ""
		}
	}

	ip6 := os.Getenv("IP6")
	if ip6 != "" {
		if validIP6 := net.ParseIP(ip6); validIP6.To16() == nil {
			ip6 = ""
		}
	}

	asNum := os.Getenv("AS")
	if asNum != "" {
		if _, err := numorstring.ASNumberFromString(asNum); err != nil {
			asNum = ""
		}
	}

	// If ip, ip6 and asNum haven't been set yet, get them from bgp
	node, err := c.Nodes().Get(meta)
	if err != nil {
		if _, ok := err.(errors.ErrorResourceDoesNotExist); !ok {
			// No other machine has registered configuration under this nodename.
			// This must be a new host with a unique nodename, which is the
			// expected behavior.
		} else {
			log.Warnf("Error connecting to node: %s", err)
		}
		//
	} else {
		bgpIP := node.Spec.BGP.IPv4Address.String()
		if ip == "" && bgpIP != "" {
			ip = bgpIP
		}
		bgpIP6 := node.Spec.BGP.IPv6Address.String()
		if ip6 == "" && bgpIP6 != "" {
			ip6 = bgpIP6
		}
		bgpASNum := node.Spec.BGP.ASNumber.String()
		if asNum == "" && bgpASNum != "" {
			asNum = bgpASNum
		}
		if bgpIP != "" && ip != "autodetect" {
			log.Info(`WARNING: Nodename '%s' is already in use with IP address %s. 
Calico requires each compute host to have a unique hostname.
If this is your first time running the Calico node on this host 
ensure that another host is not already using the same hostname.`, nodeName, bgpIP)
		}
	}

	if ip == "autodetect" {
		exclude := []string{"^docker.*", "^cbr.*", "dummy.*",
			"virbr.*", "lxcbr.*", "veth.*",
			"cali.*", "tunl.*", "flannel.*"}
		ip, err = autodetection.AutodetectIPv4(exclude)

	}

	if ip == "" {
		log.Warnf(`Couldn't autodetect a management IPv4 address. Please
provide an IP address either by configuring one in the
node resource, or by re-running the container with the
IP environment variable set.`)
		os.Exit(1)
	}

	// Write a startup environment file containing the IP address that may have
	// just been detected.
	// This is required because the confd templates expect to be able to fill in
	// some templates by fetching them from the environment.
	f, err := os.OpenFile("startup.env", os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		panic(fmt.Sprintf("Error loading config: %s", err))
	}

	f.WriteString("export IP=" + ip + "\n")
	f.WriteString("export HOSTNAME=%s" + nodeName + "\n")

	warnIfUnknownIP(ip, ip6)

	if strings.ToLower(os.Getenv("NO_DEFAULT_POOLS")) != "true" {
		poolList, err := c.IPPools().List(api.IPPoolMetadata{})
		if err != nil {
			log.Warnf("Unable to fetch IP pool list: %s", err)
			panic(err)
		}
		ipv4Present, ipv6Present := false, false
		for p := range poolList {
			s := strings.Split(p.List(api.IPPoolMetadata{}).CIDR.String(), "/")
			validIP := net.ParseIP(ip)
			if validIP.to4() != nil {
				ipv4Present = true
			} else {
				ipv6Present = true
			}
			if ipv4Present == true && ipv6Present == true {
				break
			}
		}

		if ipv4Present == false {
			_, cidr, err := net.ParseCIDR("192.168.0.0/16")
			if err != nil {
				log.Warnf("Unable to create ipv4 cidr: %s", err)
				panic(err)
			}
			ipv4Meta := api.IPPoolMetadata{CIDR: cnet.IPNet{*cidr}}
			ipv4Spec := api.IPPoolSpec{NATOutgoing: true}
			c.Apply(api.IPPool(ipv4Meta, ipv4Spec))
		}

		if _, pathErr := os.Stat("/proc/sys/net/ipv6"); ipv6Present == false && pathErr == nil {
			_, cidr, err := net.ParseCIDR("fd80:24e2:f998:72d6::/64")
			if err != nil {
				log.Warnf("Unable to create ipv6 cidr: %s", err)
			}
			ipv6Meta := api.IPPoolMetadata{CIDR: cnet.IPNet{*cidr}}
			ipv6Spec := api.IPPoolSpec{NATOutgoing: true}
			c.Apply(api.IPPool(ipv6Meta, ipv6Spec))
		}
	}

	ns := api.NodeSpec{api.NodeBGPSpec{ASNumber: asNum, IPv4Address: ip, IPv6Address, ip6}}
	nm := api.NodeMetadata{Name: nodeName}
	nc := api.Node{Metadata: nm, Spec: ns}
	n, err := c.Nodes().Create(nc)
	if err != nil {
		log.Warnf("Failed to create the node: %s", err)
		panic(err)
	}
}

func warnIfUnknownIP(ip string, ip6 string) {
	validFfaces, err := autodetection.GetValidInterfaces([]string{"docker0"})
	if err != nil {
		log.Warnf("Failed to complete IP-Interface check.")
		return
	}
	foundIP4, foundIP6 := false, false
	for _, iface := range validIfaces {
		if foundIP4 == false {
			ip4List, err := autodetection.GetIPsFromIface(iface, 4)
			if err != nil {
				log.Warnf("Failed to detect interface IPs")
			} else {
				for _, ifIP := range ipList {
					if ip == ifIP {
						foundIP4 == true
						break
					}
				}

			}
		}
		if foundIP6 == false {
			ip6List, _ := autodetection.GetIPsFromIface(iface, 6)
			if err != nil {
				log.Warnf("Failed to detect interface IPs")
			} else {
				for _, ifIP := range ip6List {
					if ip == ifIP {
						foundIP4 == true
						break
					}
				}

			}
		}
		if foundIP4 == true || foundIP6 == true {
			break
		}
	}
	if foundIP4 == false {
		fmt.Printf(`WARNING: Could not confirm that the provided IPv4 address is
assigned to this host.`)
	}
	if foundIP6 == false {
		fmt.Printf(`WARNING: Could not confirm that the provided IPv6 address is
assigned to this host.`)
	}
}

// waitForDatastore blocks until the WAIT_FOR_DATASTORE env variable
// is either absent or not set to false
func waitForDatastore() {
	fmt.Printf("Waiting for datastore connection...")
	for v := os.Getenv("WAIT_FOR_DATASTORE"); v != "false"; {
		// Hack to ensure we can connect to datastore
		_, err := c.Nodes().List(api.NodeMetadata{})
		if err != nil {
			if _, ok := err.(errors.ErrorDatastoreError); !ok {
				time.Sleep(1000 * time.Millisecond)
			} else {
				panic(fmt.Sprintf("Error loading config: %s", err))
			}
		}
	}
}

// ensureClusterGUID assigns a cluster GUID if one doesn't exist.
func ensureClusterGUID(c bapi.Client) {
	guid := hex.EncodeToString(uuid.NewV4().Bytes())
	_, err := c.Create(&model.KVPair{
		Key:   model.GlobalConfigKey{Name: "ClusterGUID"},
		Value: guid,
	})
	if err != nil {
		if _, ok := err.(errors.ErrorResourceAlreadyExists); !ok {
			log.Warnf("Failed to set ClusterGUID: %s", err)
			panic(err)
		}
		log.Infof("Using previously configured ClusterGUID")
		return
	}
	log.Infof("Assigned ClusterGUID %s", guid)
}
