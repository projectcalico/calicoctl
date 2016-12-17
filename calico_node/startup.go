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
	"os"
	"github.com/satori/go.uuid"
	"time"
	"autodetection"
	"strings"

	log "github.com/Sirupsen/logrus"
	"github.com/projectcalico/libcalico-go/lib/backend"
	"github.com/projectcalico/libcalico-go/lib/backend/api"
	"github.com/projectcalico/libcalico-go/lib/backend/model"
	"github.com/projectcalico/libcalico-go/lib/client"
	"github.com/projectcalico/libcalico-go/lib/errors"
	"github.com/projectcalico/libcalico-go/lib/numorstring"
	cnet "github.com/projectcalico/libcalico-go/lib/net"
)

func check(s string, err){ }

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
	c, err := backend.NewClient(*cfg)
	if err != nil {
		panic(fmt.Sprintf("Error creating client: %s", err))
	}
	log.Info("Ensuring datastore is initialized")
	err = c.EnsureInitialized()
	if err != nil {
		panic(fmt.Sprintf("Error initializing datastore: %s", err))
	}
	log.Info("Datastore is initialized")

	// Make sure we have a global cluster ID set.
	log.Info("Ensuring a cluster guid is set")
	ensureClusterGuid(c)

	hostname := os.GetEnv("NODENAME")
	if hostname == nil {
		hostname = os.GetEnv("HOSTNAME")
	}
	if hostname == nil {
		hostname = os.Hostname()
	}

	if d := os.Getenv("DATASTORE_TYPE"); d == "kubernetes" {
		f, err := os.OpenFile("startup.env", os.O_APPEND|os.O_WRONLY, 0600)
		if err != nil {
			panic(fmt.Sprintf("Error loading config: %s", err))
		}
		f.WriteString("export DATASTORE_TYPE=kubernetes\n")
		f.WriteString("export HOSTNAME=%s\n" % hostname)
	}

	meta := api.NodeMetaData{Name: hostname}

	fmt.Printf("Waiting for etcd connection...")
	for v := os.Getenv("WAIT_FOR_DATASTORE"); v != "false"; {
		_, err := c.Nodes().Get(meta)
		if err != nil {
			if err == errors.ErrorDatastoreError {
				time.Sleep(1000 * time.Millisecond)
			}
			else {
				panic(fmt.Sprintf("Error loading config: %s", err))
			}
		} else {
			break
		}
	}

	ip := os.Getenv("IP")

	// If IP env variable is set to 'autodetect' or not set, get all
	// valid non-excluded ifaces, then set IP to first valid IPv4 discovered.
	if ip == "autodetect" || ip == nil:
		ip = nil
		exclude = []string{"^docker.*", "^cbr.*", "dummy.*",
	                       "virbr.*", "lxcbr.*", "veth.*",
	                       "cali.*", "tunl.*", "flannel.*"}
		valid_ifaces := autodetection.GetValidInterfaces(exclude)
		if err != nil {
			panic(fmt.Sprintf("Autodetection error: %s", err))
		}

		for _, iface := range ifaces {
			ip_list, err := autodetection.GetIPsFromIface(iface, 4)
			if len(ip_list) > 0 {
				ip = ip_list[0]
				break
			}
		}

	ip6 := os.Getenv("IP6")
	if ip6 != nil {
		valid_ip := net.ParseIP(ip6)
		if valid_ip.To16() == nil {
			ip6 = nil
		}
	}

	as_num := os.Getenv("AS")
	if as_num != nil {
		as, err := numorstring.ASNumberFromString(as_num)
		if err != nil {
			as_num = nil
		}
	}

	// If ip, ip6 and as_num haven't been set yet, get them from bgp
	ns, err := c.Nodes().Get(meta)
	if err != nil {
		if err == errors.ErrorResourceDoesNotExist {
			// No other machine has registered configuration under this hostname.
			// This must be a new host with a unique hostname, which is the
			// expected behavior.
		} else {
			info.Warnf("Error connecting to node: %s", err)
		}

	} else {
		bgp_ip := ns.BGP.IPv4Address.String()
		if ip == nil && bgp_ip != nil {
			ip = bgp_ip
		}
		bgp_ip6 := ns.BGP.IPv6Address.String()
		if ip6 == nil && bgp_ip6 != nil {
			ip6 = bgp_ip6
		}
		bgp_as_num := ns.BGP.ASNumber.String()
		if as_num == nil && bgp_as_num != nil {
			as_num = bgp_as_num
		}
		if bgp_ip != nil && bgp_ip != ip {
			log.Info("WARNING: Hostname '%s' is already in use with IP address %s. 
				      Calico requires each compute host to have a unique hostname.
	                  If this is your first time running the Calico node on this host, 
	                  ensure that another host is not already using the same hostname.", 
	                  hostname, bgp_ip)
		}
	}

	if ip == nil {
		log.Warnf("Couldn't autodetect a management IPv4 address. Please
                   provide an IP address either by configuring one in the
                   node resource, or by re-running the container with the
                   IP environment variable set.")
		os.exit(1)
	} 

    // Write a startup environment file containing the IP address that may have
    // just been detected.
    // This is required because the confd templates expect to be able to fill in
    // some templates by fetching them from the environment.
	f, err := os.OpenFile("startup.env", os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		panic(fmt.Sprintf("Error loading config: %s", err))
	}

	f.WriteString("export IP=%s\n", ip)
	f.WriteString("export HOSTNAME=%s\n", hostname)

	warnIfUnknownIp(ip, ip6)

	if strings.ToLower(os.Getenv("NO_DEFAULT_POOLS")) != "true" {
		poolList, err := c.IPPools().List(api.IPPoolMetadata{})
		if err != nil {
			panic(info.Warnf("Unable to fetch IP pool list: %s", err))
		}
		ipv4_present, ipv6_present := false, false
		for p := range poolList {
			s := strings.Split(p.IPPoolMetadata.CIDR.String())
			valid_ip := net.ParseIP(ip)
			if valid_ip.to4() != nil {
				ipv4_present = true
			} else {
				ipv6_present = true
			}
			if ipv4_present == true && ipv6_present_present == true {
				break
			}
		}

		if ipv4_present == false {
			_, cidr, err := net.ParseCIDR("192.168.0.0/16")
			if err != nil {
				panic(info.Warnf("Unable to create ipv4 cidr: %s", err))
			}
  			ipv4_meta = api.IPPoolMetadata{CIDR: cnet.IPNet{*cidr}}			
  			c.Apply(api.IPPool(ipv4_meta))
		}

		if _, path_err := os.Stat("/proc/sys/net/ipv6"); ipv6_present == false && path_err == nil {
			_, cidr, err := net.ParseCIDR("fd80:24e2:f998:72d6::/64")
			if err != nil {
				info.Warnf("Unable to create ipv6 cidr: %s", err)
			}
  			ipv6_meta = api.IPPoolMetadata{CIDR: cnet.IPNet{*cidr}}			
  			c.Apply(api.IPPool(ipv6_meta))
		}
	}

	ns := api.NodeSpec{api.NodeBGPSpec{ASNumber: as_num, IPv4Address: ip, IPv6Address, ip6}}
	nm := api.NodeMetadata{Name: hostname}
	n := api.Node{Metadata: nm, Spec: ns}
	n, err : = c.Nodes().Create(n)
	if err != nil{
		panic(info.Warnf("Failed to create the node: %s", err))
	}
	




	
		
		
	}

func warnIfUnknownIp(ip, ip6) {
	valid_ifaces, err := autodetection.GetValidInterfaces([]string{"docker0"})
	if err != nil {
		log.Warnf("Failed to complete IP-Interface check.")
		return
	}
	found_ip4, found_ip6 := false, false
	for _, iface := range valid_ifaces {
		if found_ip4 == false {
			ip4_list, err := autodetection.GetIPsFromIface(iface, 4)
			if err != nil{
				log.Warnf("Failed to detect interface IPs")
			} else {
				for _, if_ip := range ip_list {
					if ip == if_ip {
						found_ip4 == true
						break
					} 
				}

			}
		}
		if found_ip6 == false {
			ip6_list, _ := autodetection.GetIPsFromIface(iface, 6)
			if err != nil{
				log.Warnf("Failed to detect interface IPs")
			} else {
				for _, if_ip := range ip6_list {
					if ip == if_ip {
						found_ip4 == true
						break
					} 
				}

			}
		}
		if found_ip4 == true || found_ip6 == true{
			break
		}
	if found_ip4 == false {
		fmt.Printf("WARNING: Could not confirm that the provided IPv4 address is
                   assigned to this host.")
	}
	if found_ip6 == false {
		fmt.Printf("WARNING: Could not confirm that the provided IPv6 address is
                   assigned to this host.")
	}
}


// ensureClusterGuid assigns a cluster GUID if one doesn't exist.
func ensureClusterGuid(c api.Client) {
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
