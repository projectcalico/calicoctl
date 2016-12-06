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
	"io/ioutil"
	"net/http"
	"os"

	log "github.com/Sirupsen/logrus"
	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/backend"
	bapi "github.com/projectcalico/libcalico-go/lib/backend/api"
	"github.com/projectcalico/libcalico-go/lib/backend/model"
	"github.com/projectcalico/libcalico-go/lib/client"
	"github.com/projectcalico/libcalico-go/lib/errors"
	"github.com/projectcalico/libcalico-go/lib/net"
	"github.com/satori/go.uuid"
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

	// Update the Node resource if necessary.
	log.Info("Updating node resource")
	updateNodeResource()
}

// ensureClusterGuid assigns a cluster GUID if one doesn't exist.
func ensureClusterGuid(c bapi.Client) {
	guid := hex.EncodeToString(uuid.NewV4().Bytes())
	_, err := c.Create(&model.KVPair{
		Key:   model.GlobalConfigKey{Name: "ClusterGUID"},
		Value: guid,
	})
	if err != nil {
		if _, ok := err.(errors.ErrorResourceAlreadyExists); !ok {
			log.WithError(err).Warn("Failed to set ClusterGUID")
			panic(err)
		}
		log.Infof("Using previously configured ClusterGUID")
		return
	}
	log.Infof("Assigned ClusterGUID %s", guid)
}

// Update the current Node resource configuration (if it exists).
func updateNodeResource() {
	var c *client.Client
	var err error
	var node *api.Node
	var modified bool

	if cfg, err := client.LoadClientConfig(""); err != nil {
		panic(fmt.Sprintf("Error loading config: %s", err))
	} else if c, err = client.New(*cfg); err != nil {
		panic(fmt.Sprintf("Error creating client: %s", err))
	}

	// Get the current Node resource configuration.  If it doesn't exist,
	// initialise it now.
	nm := api.NodeMetadata{Name: os.Getenv("NODENAME")}
	if node, err = c.Nodes().Get(nm); err != nil {
		if _, ok := err.(errors.ErrorResourceDoesNotExist); !ok {
			panic(fmt.Sprintf("Error contacting datastore: %s", err))
		} else {
			log.WithField("Name", nm.Name).Info("Node has not yet been configured")
			node = &api.Node{Metadata: nm}
			modified = true
		}
	}
	log.Infof("Current node config: %v", node)

	// Check to see if we are on AWS, and if so get the IPv4 and IPv6
	// subnets (if they have not yet been configured).
	if node.Spec.BGP != nil {
		log.Infof("BGP configuration is specified")

		// OR IF ENV IS SET TO autodiscover
		needv4 := (node.Spec.BGP.IPv4Address != nil && node.Spec.BGP.IPv4Network == nil)
		needv6 := (node.Spec.BGP.IPv6Address != nil && node.Spec.BGP.IPv6Network == nil)

		if needv4 || needv6 {
			v4, v6 := getAWSSubnets()
			if needv4 && v4 != nil {
				log.Info("Setting IPv4 network")
				node.Spec.BGP.IPv4Network = v4
				modified = true
			}
			if needv6 && v6 != nil {
				log.Info("Setting IPv6 network")
				node.Spec.BGP.IPv6Network = v6
				modified = true
			}
		}
	}

	// If the node was modified, then apply the updated config.
	if modified {
		log.Info("Updating node config")
		if _, err = c.Nodes().Apply(node); err != nil {
			log.WithError(err).Fatal("Unable to update node config")
		}
	}
}

// getAWSVPCNetworks() returns the (IPv4, IPv6) CIDRS (in IPNet form) on an AWS
// VPC deployment.
//
// Returns nil, nil if the deployment is not AWS, or if the metadata service is
// unavailable.
func getAWSSubnets() (*net.IPNet, *net.IPNet) {
	mac, err := getAWSMetadata("mac")
	if err != nil {
		log.Info("Unable to query AWS metadata service")
		return nil, nil
	}
	log.WithField("mac", mac).Info("Found MAC from metadata service")

	var ipnetv4, ipnetv6 *net.IPNet
	if netv4, err := getAWSMetadata("network/interfaces/macs/" + mac + "/subnet-ipv4-cidr-block"); err == nil {
		if _, ipnetv4, err = net.ParseCIDR(netv4); err != nil {
			log.WithError(err).Infof("Cannot parse subnet IPv4 CIDR: %s", netv4)
		}
	}
	if netv6, err := getAWSMetadata("network/interfaces/macs/" + mac + "/subnet-ipv6-cidr-block"); err == nil {
		if _, ipnetv6, err = net.ParseCIDR(netv6); err != nil {
			log.WithError(err).Infof("Cannot parse subnet IPv6 CIDR: %s", netv6)
		}
	}

	log.WithFields(log.Fields{"IPv4Net": ipnetv4, "IPv6Net": ipnetv6}).Info("Found IP subnets")
	return ipnetv4, ipnetv6
}

func getAWSMetadata(md string) (string, error) {
	resp, err := http.Get("http://169.254.169.254/latest/meta-data/" + md)
	defer resp.Body.Close()
	if err != nil {
		return "", err
	}
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("Received status code %d", resp.StatusCode)
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}
