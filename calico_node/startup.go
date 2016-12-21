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
	"fmt"
	"io/ioutil"
	"os"
	"strconv"
	"strings"
	"time"

	log "github.com/Sirupsen/logrus"
	"github.com/projectcalico/calicoctl/calico_node/autodetection"
	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/client"
	"github.com/projectcalico/libcalico-go/lib/errors"
	"github.com/projectcalico/libcalico-go/lib/net"
	"github.com/projectcalico/libcalico-go/lib/numorstring"
)

const (
	DEFAULT_IPV4_POOL_CIDR = "192.168.0.0/16"
	DEFAULT_IPV6_POOL_CIDR = "fd80:24e2:f998:72d6::/64"
)

// This file contains the main startup processing for the calico/node.  This
// includes:
// -  Detecting IP address and Network to use for BGP
// -  Configuring the node resource with IP/AS information provided in the
//    environment, or autodetected.
// -  Creating default IP Pools for quick-start use
// -  TODO:  Configuring IPIP tunnel with an IP address from an IP pool
// TODO: Different auto-detection methods

func main() {
	var err error

	// Determine the name for this node.
	nodeName := determineNodeName()

	// Create the Calico API client.
	cfg, client := createClient()

	// If this is a Kubernetes backed datastore then just make sure the
	// datastore is initialized and then exit.  We don't need to explicitly
	// initialize the datastore for non-Kubernetes because the node resource
	// management will do that for us.
	if cfg.Spec.DatastoreType == api.Kubernetes {
		message("Calico is using a Kubernetes datastore")
		err = client.EnsureInitialized()
		if err != nil {
			fatal("Error initializing Kubernetes as the datastore: %s", err)
			terminate()
		}
		log.Info("Kubernetes is initialized as a Calico datastore")
		writeStartupEnv(nodeName, "", "")
		return
	}

	// Query the current Node resources.  We update our node resource with
	// updated IP data and use the full list of nodes for validation.
	node := getNode(client, nodeName)

	// If running in policy only mode, apply the node resource and exit.
	// This ensures we have an entry that can be queried, and also ensures
	// the datastore is initialized.
	if strings.ToLower(os.Getenv("CALICO_NETWORKING_BACKEND")) == "none" {
		if _, err := client.Nodes().Apply(node); err != nil {
			fatal("Unable to set node resource configuration: %s", err)
			terminate()
		}
		message("Running calico/node in policy only mode")
		writeStartupEnv(nodeName, "", "")
		return
	}

	// Configure and verify the node IP addresses and subnets.
	configureIPsAndSubnets(node)

	// Configure the node AS number.
	configureASNumber(node)

	// Configure IP Pool configuration.
	configureIPPools(client)

	// Check for conflicting node configuration
	checkConflictingNodes(client, node)

	// Apply the updated node resource.
	if _, err := client.Nodes().Apply(node); err != nil {
		fatal("Unable to set node resource configuration: %s", err)
		terminate()
	}

	// Set other Felix config that is not yet in the node resource.
	if err := ensureDefaultConfig(client, node); err != nil {
		fatal("Unable to set global default configuration: %s", err)
		terminate()
	}

	// Write the startup.env file now that we are ready to start other
	// components.
	ipv6Str := ""
	if node.Spec.BGP.IPv6Address != nil {
		ipv6Str = node.Spec.BGP.IPv6Address.String()
	}
	writeStartupEnv(nodeName, node.Spec.BGP.IPv4Address.String(), ipv6Str)

	// Tell the user what the name of the node is.
	message("Using node name: %s", nodeName)
}

// determineNodeName is called to determine the node name to use for this instance
// of calico/node.
func determineNodeName() string {
	// Determine the name of this node.
	nodeName := os.Getenv("NODENAME")
	if nodeName == "" {
		// NODENAME not specified, check HOSTNAME (we maintain this for
		// backwards compatibility).
		log.Info("NODENAME environment not specified - check HOSTNAME")
		nodeName = os.Getenv("HOSTNAME")
	}
	if nodeName == "" {
		// The node name has not been specified.  We need to use the OS
		// hostname - but should warn the user that this is not a
		// recommended way to start the node container.
		var err error
		if nodeName, err = os.Hostname(); err != nil {
			log.Info("Unable to determine hostname - exiting")
			panic(err)
		}

		message("******************************************************************************")
		message("* WARNING                                                                    *")
		message("* Auto-detecting node name.  It is recommended that an explicit fixed value  *")
		message("* is supplied using the NODENAME environment variable.  Using a fixed value  *")
		message("* ensures that any changes to the compute host's hostname will not affect    *")
		message("* the Calico configuration when the Calico node restarts.                    *")
		message("******************************************************************************")
	}
	return nodeName
}

// createClient() creates the Calico API client, and unless requested otherwise,
// checks that the client is accessible.
func createClient() (*api.CalicoAPIConfig, *client.Client) {
	log.Info("Loading client config")
	cfg, err := client.LoadClientConfig("")
	if err != nil {
		fatal("Error loading datastore config: %s", err)
		terminate()
	}

	log.Info("Creating client")
	client, err := client.New(*cfg)
	if err != nil {
		fatal("Error accessing the Calico datastore: %s", err)
		terminate()
	}

	// An explicit value of false is required to skip waiting for the
	// datastore.
	if os.Getenv("WAIT_FOR_DATASTORE") == "false" {
		message("Skipping datastore connection test")
		return cfg, client
	}

	message("Checking datastore connection")
	for i := 0; i <= 120; i++ {
		// Query some arbitrary configuration to see if the connection
		// is working.  Getting a specific node is a good option, even
		// if the node does not exist.
		_, err = client.Nodes().Get(api.NodeMetadata{Name: "foo"})

		// We only care about a couple of error cases, all others would
		// suggest the datastore is accessible.
		if err != nil {
			switch err.(type) {
			case errors.ErrorConnectionUnauthorized:
				fatal("Connection to the datastore is unauthorized")
				terminate()
			case errors.ErrorDatastoreError:
				time.Sleep(1000 * time.Millisecond)
				continue
			}
		}

		err = nil
		break
	}
	if err != nil {
		fatal("Connection to the datastore has failed: %s", err)
		terminate()
	}

	message("Datastore connection verified")

	return cfg, client
}

// writeStartupEnv writes out the startup.env file to set environment variables
// that are required by confd/bird etc. but may not have been passed into the
// container.
func writeStartupEnv(nodeName string, ip string, ip6 string) {
	text := "export HOSTNAME=" + nodeName + "\n"
	text += "export NODENAME=" + nodeName + "\n"
	text += "export IP=" + ip + "\n"
	text += "export IP6=" + ip6 + "\n"

	// Write out the startup.env file to ensure require environments are
	// set (which they might not otherwise be).
	if err := ioutil.WriteFile("startup.env", []byte(text), 0666); err != nil {
		log.WithError(err).Info("Unable to write to startup.env")
		fatal("Unable to write to local filesystem")
		terminate()
	}
}

// getNode returns the current node configuration and a list of all configured
// nodes.  If this node has not yet been created, it returns a blank node
// resource.
func getNode(client *client.Client, nodeName string) *api.Node {
	meta := api.NodeMetadata{Name: nodeName}
	node, err := client.Nodes().Get(meta)

	if err != nil {
		if _, ok := err.(errors.ErrorResourceDoesNotExist); !ok {
			log.WithError(err).WithField("Name", nodeName).Info("Unable to query node configuration")
			fatal("Unable to access datastore to query node configuration")
			terminate()
		}

		log.WithField("Name", nodeName).Info("Returning empty node configuration")
		node = &api.Node{Metadata: api.NodeMetadata{Name: nodeName}}
	}

	return node
}

// configureIPsAndSubnets updates the supplied node resource with IP and Subnet
// information to use for BGP.
func configureIPsAndSubnets(node *api.Node) {
	// If the node resource currently has no BGP configuration, add an empty
	// set of configuration as it makes the processing below easier, and we
	// must end up configuring some BGP fields before we complete.
	if node.Spec.BGP == nil {
		log.Info("Initialise BGP data")
		node.Spec.BGP = &api.NodeBGPSpec{}
	}

	// Determine the autodetection type for IPv4 and IPv6.  Note that we
	// only autodetect IPv4 when it has not been specified.  IPv6 must be
	// explicitly requested using the "autodetect" value.
	//
	// If we aren't auto-detecting then we need to validate the configured
	// value and possibly fix up missing subnet configuration.
	ipv4Env := os.Getenv("IP")
	if ipv4Env == "autodetect" || (ipv4Env == "" && node.Spec.BGP.IPv4Address == nil) {
		adm := os.Getenv("IP_AUTODETECT_METHOD")
		//node.Spec.BGP.IPv4Address, node.Spec.BGP.IPv4Network = autoDetectIPAndNetwork(adm, 4)
		node.Spec.BGP.IPv4Address, _ = autoDetectIPAndNetwork(adm, 4)

		// We must have an IPv4 address configured for BGP to run.
		if node.Spec.BGP.IPv4Address == nil {
			fatal("Couldn't autodetect a management IPv4 address:")
			message("  -  provide an IP address by configuring one in the node resource, or")
			message("  -  provide an IP address using the IP environment, or")
			message("  -  if auto-detecting, use a different autodetection method.")
			terminate()
		}

	} else {
		node.Spec.BGP.IPv4Address, _ = fetchAndValidateIPAndNetwork(
			ipv4Env, 4,
			node.Spec.BGP.IPv4Address, nil)
	}

	ipv6Env := os.Getenv("IP6")
	if ipv6Env == "autodetect" {
		adm := os.Getenv("IP6_AUTODETECT_METHOD")
		//node.Spec.BGP.IPv6Address, node.Spec.BGP.IPv6Network = autoDetectIPAndNetwork(adm, 6)
		node.Spec.BGP.IPv6Address, _ = autoDetectIPAndNetwork(adm, 6)
	} else {
		node.Spec.BGP.IPv6Address, _ = fetchAndValidateIPAndNetwork(
			ipv6Env, 6,
			node.Spec.BGP.IPv6Address, nil)
	}

}

// fetchAndValidateIPAndNetwork fetches and validates the IP configuration from
// either the environments, from pre-configured values.  In addition, missing
// network is autodetected from the interface configuration based on the configured
// IP address.
func fetchAndValidateIPAndNetwork(ipEnv string, version int, ip *net.IP, ipNet *net.IPNet) (*net.IP, *net.IPNet) {
	// If we don't yet have an IP and an IP has not been specified, return
	// the existing values.
	if ip == nil && ipEnv == "" {
		return ip, ipNet
	}

	// If an IP address has been specified in the environment, attempt to
	// extract the IP and possibly the subnet if that was also included.
	if ipEnv != "" {
		log.WithField("IP Env", ipEnv).Info("Using specified IP address")

		// We allow the IP address env to contain the subnet as well.
		var err error
		if strings.Contains(ipEnv, "/") {
			ip, ipNet, err = net.ParseCIDR(ipEnv)
			if err != nil {
				message("Using IPv%d address from environment: %s", ip.Version(), ipEnv)
				message("Using IPv%d network from environment: %s", ip.Version(), ipEnv)
			}
		} else {
			ip = &net.IP{}
			err = ip.UnmarshalText([]byte(ipEnv))
			if err != nil {
				message("Using IPv%d address from environment: %s", ip.Version(), ipEnv)
			}
		}

		if err != nil {
			fatal("IP address '%s' is not valid", ip)
			terminate()
		}
		if ip.Version() != version {
			fatal("IP address '%s' version is incorrect, should be IPv%d", ip, version)
			terminate()
		}
	} else {
		message("Using IPv%d address configured in node: %s", ip.Version(), ip)
		if ipNet != nil {
			message("Using IPv%d network configured in node: %s", ipNet.Version(), ipNet)
		}
	}

	// Get a complete list of interfaces with their addresses.  We use this
	// to validate the IP address being used, and to update the subnet if it
	// is not specified.
	ifaces, err := autodetection.GetInterfaces(nil, nil, version)
	if err != nil {
		fatal("Unable to query host interfaces: %s", err)
		terminate()
	}
	if len(ifaces) == 0 {
		message("No interfaces found for validating IP configuration")
	}

	found := false
outer:
	for _, i := range ifaces {
		for _, a := range i.Addrs {
			if ip.Equal(a.IPAddress.IP) {
				// Found the IP address.  Either set or validate
				// the subnet.
				if ipNet == nil {
					message("Using IPv%d network discovered on interface %s: %s",
						version, i.Name, a.IPNetwork)
					ipNet = a.IPNetwork
				} else if a.IPNetwork == nil {
					warning("Unable to confirm configured network %s matches interface %s",
						ipNet, i.Name)
				} else if netEqual(ipNet, a.IPNetwork) {
					warning("Configured network %s does not match network %s on interface %s",
						ipNet, a.IPNetwork, i.Name)
				}

				found = true
				break outer
			}
		}
	}
	if !found {
		warning("Unable to confirm IP address %s is assigned to this host", ip)
	}

	return ip, ipNet
}

// autoDetectIPAndNetwork auto-detects the IP and Network using the requested
// detection method.
func autoDetectIPAndNetwork(detectionMethod string, version int) (*net.IP, *net.IPNet) {
	incl := []string{}
	excl := []string{"^docker.*", "^cbr.*", "dummy.*",
		"virbr.*", "lxcbr.*", "veth.*", "lo",
		"cali.*", "tunl.*", "flannel.*"}

	iface, addr, err := autodetection.FilteredEnumeration(incl, excl, version)
	if err != nil {
		message("Unable to auto-detect any valid interfaces: %s", err)
		return nil, nil
	}

	if addr == nil {
		message("Unable to auto-detect an IPv%d address", version)
		return nil, nil
	}

	message("Using autodetected IPv%d address on interface %s: %s", version, iface.Name, addr.IPAddress)

	if addr.IPNetwork != nil {
		message("Unable to auto-detect an IPv%d network", version)
	} else {
		message("Using autodetected IPv%d network on interface %s: %s", version, iface.Name, addr.IPNetwork)
	}

	return addr.IPAddress, addr.IPNetwork
}

// configureASNumber configures the Node resource with the AS numnber specified
// in the environment.
func configureASNumber(node *api.Node) {
	// Extract the AS number from the environment
	asStr := os.Getenv("AS")
	if asStr != "" {
		if asNum, err := numorstring.ASNumberFromString(asStr); err != nil {
			fatal("The AS number specified in the environment is not valid: %s", asStr)
			terminate()
		} else {
			message("Using AS number specified in environment: %s", asNum)
			node.Spec.BGP.ASNumber = &asNum
		}
	} else {
		message("AS number not specified in environment, using current value")
	}
}

// configureIPPools ensures that default IP pools are created (unless explicitly
// requested otherwise).
func configureIPPools(client *client.Client) {
	if strings.ToLower(os.Getenv("NO_DEFAULT_POOLS")) == "true" {
		log.Info("Not required to configured IP pools")
		return
	}

	// Get a list of all IP Pools
	poolList, err := client.IPPools().List(api.IPPoolMetadata{})
	if err != nil {
		fatal("Unable to fetch IP pool list: %s", err)
		terminate()
	}

	// Check for IPv4 and IPv6 pools and filter for IPIP pools.
	ipv4Present := false
	ipv6Present := false
	for _, p := range poolList.Items {
		version := p.Metadata.CIDR.Version()
		ipv4Present = ipv4Present || (version == 4)
		ipv6Present = ipv6Present || (version == 6)
		if ipv4Present && ipv6Present {
			break
		}
	}

	// Ensure there are pools created for each IP version.
	if !ipv4Present {
		createIPPool(client, DEFAULT_IPV4_POOL_CIDR)
	}
	if !ipv6Present && ipv6Supported() {
		createIPPool(client, DEFAULT_IPV6_POOL_CIDR)
	}
}

// ipv6Supported returns true if IPv6 is supported on this platform.  This performs
// a simplistic check of /proc/sys/net/ipv6 since platforms that do not have IPv6
// compiled in will not have this entry.
func ipv6Supported() bool {
	_, err := os.Stat("/proc/sys/net/ipv6")
	supported := (err == nil)
	log.Infof("IPv6 supported on this platform: %v", supported)
	return supported
}

// createIPPool creates an IP pool using the specified CIDR string.
func createIPPool(client *client.Client, cs string) {
	_, cidr, _ := net.ParseCIDR(cs)
	version := cidr.Version()

	log.Info("Creating default IPv%d pool", version)
	pool := &api.IPPool{
		Metadata: api.IPPoolMetadata{
			CIDR: *cidr,
		},
		Spec: api.IPPoolSpec{
			NATOutgoing: true,
		},
	}
	if _, err := client.IPPools().Apply(pool); err != nil {
		if _, ok := err.(errors.ErrorResourceAlreadyExists); !ok {
			fatal("Failed to create default IPv%d IP pool: %s", version, err)
			terminate()
		}
	}
	message("Created default IPv%d pool (%s) with NAT outgoing enabled", version, cidr)
}

// Check whether any other nodes have been configured with the same IP addresses.
func checkConflictingNodes(client *client.Client, node *api.Node) {
	// Get the full set of nodes.
	var nodes []api.Node
	if nodeList, err := client.Nodes().List(api.NodeMetadata{}); err != nil {
		fatal("Unable to query node confguration: %s", err)
		terminate()
	} else {
		nodes = nodeList.Items
	}

	ourIPv4 := node.Spec.BGP.IPv4Address
	ourIPv6 := node.Spec.BGP.IPv6Address
	errored := false
	for _, theirNode := range nodes {
		if theirNode.Spec.BGP == nil {
			// Skip nodes that don't have BGP configured.  We know
			// that this node does have BGP since we only perform
			// this check after configuring BGP.
			continue
		}
		theirIPv4 := theirNode.Spec.BGP.IPv4Address
		theirIPv6 := theirNode.Spec.BGP.IPv6Address

		// If this is our node (based on the name), check if the IP
		// addresses have changed.  If so warn the user as it could be
		// an indication of multiple nodes using the same name.  This
		// is not an error condition as the IPs could actually change.
		if theirNode.Metadata.Name == node.Metadata.Name {
			if theirIPv4 != nil && !theirIPv4.Equal(ourIPv4.IP) {
				warning("Calico node '%s' IPv4 address has changed:",
					theirNode.Metadata.Name)
				message(" -  This could happen if multiple nodes are configured with the same name")
				message(" -  Original IP: %s", theirIPv4)
				message(" -  Updated IP: %s", ourIPv4)
			}
			if theirIPv6 != nil && ourIPv6 != nil && !theirIPv6.Equal(ourIPv6.IP) {
				warning("Calico node '%s' IPv6 address has changed:",
					theirNode.Metadata.Name)
				message(" -  This could happen if multiple nodes are configured with the same name")
				message(" -  Original IP: %s", theirIPv6)
				message(" -  Updated IP: %s", ourIPv6)
			}
			continue
		}

		// Check that other nodes aren't using the same IP addresses.
		// This is an error condition.
		if theirIPv4 != nil && theirIPv4.Equal(ourIPv4.IP) {
			message("Calico node '%s' is already using the IPv4 address %s:",
				theirNode.Metadata.Name, ourIPv4)
			message(" -  Check the node configuration to remove the IP address conflict")
			errored = true
		}
		if theirIPv6 != nil && theirIPv6.Equal(ourIPv6.IP) {
			message("Calico node '%s' is already using the IPv6 address %s:",
				theirNode.Metadata.Name, ourIPv6)
			message(" -  Check the node configuration to remove the IP address conflict")
			errored = true
		}
	}

	if errored {
		terminate()
	}
}

func ensureDefaultConfig(c *client.Client, node *api.Node) error {
	// By default we set the global reporting interval to 0 - this is
	// different from the defaults defined in Felix.
	//
	// Logging to file is disabled in the felix.cfg config file.  This
	// should always be disabled for calico/node.  By default we log to
	// screen - set the default logging value that we desire.
	if err := ensureGlobalFelixConfig(c, "ReportingIntervalSecs", "0"); err != nil {
		return err
	} else if err = ensureGlobalFelixConfig(c, "LogSeverityScreen", client.GlobalDefaultLogLevel); err != nil {
		return err
	}

	// Set the default values for some of the global BGP config values and
	// per-node directory structure.
	// These are required by both confd and the GoBGP daemon.  Some of this
	// can only be done directly by the backend (since it requires access to
	// datastore features not exposed in the main API).
	//
	// TODO: This is only required for the current BIRD and GoBGP integrations,
	//       but should be removed once we switch over to a better watcher interface.
	if err := ensureGlobalBGPConfig(c, "node_mesh", fmt.Sprintf("{\"enabled\": %v}", client.GlobalDefaultNodeToNodeMesh)); err != nil {
		return err
	} else if err := ensureGlobalBGPConfig(c, "as_num", strconv.Itoa(client.GlobalDefaultASNumber)); err != nil {
		return err
	} else if err = ensureGlobalBGPConfig(c, "loglevel", client.GlobalDefaultLogLevel); err != nil {
		return err
	} else if err = ensureGlobalBGPConfig(c, "LogSeverityScreen", client.GlobalDefaultLogLevel); err != nil {
		return err
	} else if err = c.Backend.EnsureCalicoNodeInitialized(node.Metadata.Name); err != nil {
		return err
	}
	return nil
}

// ensureGlobalFelixConfig ensures that the supplied global felix config value
// is initialized, and if not initialize it with the supplied default.
func ensureGlobalFelixConfig(c *client.Client, key, def string) error {
	if val, assigned, err := c.Config().GetFelixConfig(key, ""); err != nil {
		return err
	} else if !assigned {
		return c.Config().SetFelixConfig(key, "", def)
	} else {
		log.Infof("Global Felix value already assigned %s=%s", key, val)
		return nil
	}
}

// ensureGlobalBGPConfig ensures that the supplied global BGP config value
// is initialized, and if not initialize it with the supplied default.
func ensureGlobalBGPConfig(c *client.Client, key, def string) error {
	if val, assigned, err := c.Config().GetBGPConfig(key, ""); err != nil {
		return err
	} else if !assigned {
		return c.Config().SetBGPConfig(key, "", def)
	} else {
		log.Infof("Global BGP value already assigned %s=%s", key, val)
		return nil
	}
}

// message() prints a message to screen and to log.  A newline terminator is
// not required in the format string.
func message(format string, args ...interface{}) {
	fmt.Printf(format+"\n", args...)
	log.Infof(format, args...)
}

// warning() prints a warning to screen and to log.  A newline terminator is
// not required in the format string.
func warning(format string, args ...interface{}) {
	fmt.Printf("WARNING: "+format+"\n", args...)
	log.Warnf(format, args...)
}

// fatal() prints a fatal message to screen and to log.  A newline terminator is
// not required in the format string.
func fatal(format string, args ...interface{}) {
	fmt.Printf("ERROR: "+format+"\n", args...)
	log.Errorf(format, args...)
}

// terminate() prints a terminate message and exists with status 1.
func terminate() {
	message("Terminating")
	os.Exit(1)
}

// netEqual returns true if the two networks are equal.  Neither network
// can be nil.
func netEqual(net1, net2 *net.IPNet) bool {
	return net1.String() == net2.String()
}
