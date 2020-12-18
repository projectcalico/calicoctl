// Copyright (c) 2016-2020 Tigera, Inc. All rights reserved.

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

package ipam

import (
	"context"
	"fmt"
	"net"
	"strings"

	docopt "github.com/docopt/docopt-go"
	"github.com/projectcalico/libcalico-go/lib/ipam"
	"k8s.io/client-go/kubernetes"

	apiv3 "github.com/projectcalico/libcalico-go/lib/apis/v3"
	"github.com/projectcalico/libcalico-go/lib/backend/k8s"
	"github.com/projectcalico/libcalico-go/lib/backend/model"
	"github.com/projectcalico/libcalico-go/lib/clientv3"
	cnet "github.com/projectcalico/libcalico-go/lib/net"

	bapi "github.com/projectcalico/libcalico-go/lib/backend/api"
	"github.com/projectcalico/libcalico-go/lib/options"

	"github.com/projectcalico/calicoctl/v3/calicoctl/commands/constants"
	"github.com/projectcalico/calicoctl/v3/calicoctl/util"

	"github.com/projectcalico/calicoctl/v3/calicoctl/commands/clientmgr"
)

// IPAM takes keyword with an IP address then calls the subcommands.
func Check(args []string) error {
	doc := constants.DatastoreIntro + `Usage:
  <BINARY_NAME> ipam check [--config=<CONFIG>] [--show-ips]

Options:
  -h --help                Show this screen.
  -c --config=<CONFIG>     Path to the file containing connection configuration in
                           YAML or JSON format.
                           [default: ` + constants.DefaultConfigPath + `]

Description:
  The ipam check command checks the integrity of the IPAM datastructures against Kubernetes.
`
	// Replace all instances of BINARY_NAME with the name of the binary.
	name, _ := util.NameAndDescription()
	doc = strings.ReplaceAll(doc, "<BINARY_NAME>", name)

	parsedArgs, err := docopt.Parse(doc, args, true, "", false, false)
	if err != nil {
		return fmt.Errorf("Invalid option: 'calicoctl %s'. Use flag '--help' to read about a specific subcommand.", strings.Join(args, " "))
	}
	if len(parsedArgs) == 0 {
		return nil
	}
	ctx := context.Background()

	// Create a new backend client from env vars.
	cf := parsedArgs["--config"].(string)
	client, err := clientmgr.NewClient(cf)
	if err != nil {
		return err
	}

	// Get the backend client.
	type accessor interface {
		Backend() bapi.Client
	}
	bc, ok := client.(accessor).Backend().(*k8s.KubeClient)
	if !ok {
		return fmt.Errorf("IPAM check only supports Kubernetes Datastore Driver")
	}
	kubeClient := bc.ClientSet
	showIPs := parsedArgs["--show-ips"].(bool)
	checker := NewIPAMChecker(kubeClient, client, bc, showIPs)

	return checker.checkIPAM(ctx)
}

func NewIPAMChecker(k8sClient kubernetes.Interface,
	v3Client clientv3.Interface,
	backendClient bapi.Client,
	showIPs bool) *IPAMChecker {
	return &IPAMChecker{
		allocations: map[string][]allocation{},
		inUseIPs:    map[string][]ownerRecord{},

		k8sClient:     k8sClient,
		v3Client:      v3Client,
		backendClient: backendClient,

		showIPs: showIPs,
	}
}

type IPAMChecker struct {
	allocations map[string][]allocation
	inUseIPs    map[string][]ownerRecord

	k8sClient     kubernetes.Interface
	backendClient bapi.Client
	v3Client      clientv3.Interface

	showIPs bool
}

func (c *IPAMChecker) checkIPAM(ctx context.Context) error {
	{
		fmt.Println("Loading all IPAM blocks...")
		blocks, err := c.backendClient.List(ctx, model.BlockListOptions{}, "")
		if err != nil {
			return fmt.Errorf("failed to list IPAM blocks: %w", err)
		}
		fmt.Printf("Found %d IPAM blocks.\n", len(blocks.KVPairs))

		for _, kvp := range blocks.KVPairs {
			b := kvp.Value.(*model.AllocationBlock)
			for ord, attrIdx := range b.Allocations {
				if attrIdx == nil {
					continue // IP is not allocated
				}
				c.recordAllocation(b, ord)
			}
		}
		fmt.Printf("IPAM blocks record %d allocations.\n", len(c.allocations))
	}
	var activeIPPools []*cnet.IPNet
	{
		fmt.Println("Loading all IPAM pools...")
		ipPools, err := c.v3Client.IPPools().List(ctx, options.ListOptions{})
		if err != nil {
			return fmt.Errorf("failed to load IP pools: %w", err)
		}
		for _, p := range ipPools.Items {
			if p.Spec.Disabled {
				continue
			}
			_, cidr, err := cnet.ParseCIDR(p.Spec.CIDR)
			if err != nil {
				return fmt.Errorf("failed to parse IP pool CIDR: %w", err)
			}
			activeIPPools = append(activeIPPools, cidr)
		}
		fmt.Printf("Found %d active IP pools.\n", len(activeIPPools))
	}
	{
		fmt.Println("Loading all nodes.")
		nodes, err := c.v3Client.Nodes().List(ctx, options.ListOptions{})
		if err != nil {
			return fmt.Errorf("failed to list nodes: %w", err)
		}
		numNodeIPs := 0
		for _, n := range nodes.Items {
			ips, err := getNodeIPs(n)
			if err != nil {
				return err
			}
			for _, ip := range ips {
				c.recordInUseIP(ip, n, fmt.Sprintf("Node(%s)", n.Name))
				numNodeIPs++
			}
		}
		fmt.Printf("Found %d node tunnel IPs.\n", numNodeIPs)
	}

	{
		fmt.Println("Loading all workload endpoints.")
		weps, err := c.v3Client.WorkloadEndpoints().List(ctx, options.ListOptions{})
		if err != nil {
			return fmt.Errorf("failed to list workload endpoints: %w", err)
		}
		numNodeIPs := 0
		for _, w := range weps.Items {
			ips, err := getWEPIPs(w)
			if err != nil {
				return err
			}
			for _, ip := range ips {
				c.recordInUseIP(ip, w, fmt.Sprintf("Workload(%s/%s)", w.Namespace, w.Name))
				numNodeIPs++
			}
		}
		fmt.Printf("Found %d workload IPs.\n", numNodeIPs)
		fmt.Printf("Workloads and nodes are using %d IPs.\n", len(c.inUseIPs))
	}

	var allocatedButNotInUseIPs []string
	{
		fmt.Printf("Scanning for IPs that are allocated but not actually in use...\n")
		for ip, _ := range c.allocations {
			if _, ok := c.inUseIPs[ip]; !ok {
				if c.showIPs {
					fmt.Printf("  %s allocated in IPAM but found now owner.\n", ip)
				}
				allocatedButNotInUseIPs = append(allocatedButNotInUseIPs, ip)
			}
		}
		fmt.Printf("Found %d IPs that are allocated in IPAM but not actually in use.\n", len(allocatedButNotInUseIPs))
	}

	var inUseButNotAllocatedIPs []string
	var nonCalicoIPs []string
	{
		fmt.Printf("Scanning for IPs that are in use by a workload or node but not allocated in IPAM...\n")
		for ip, owners := range c.inUseIPs {
			if c.showIPs && len(owners) > 1 {
				fmt.Printf("  %s has multiple owners.\n", ip)
			}
			if _, ok := c.allocations[ip]; !ok {
				found := false
				parsedIP := net.ParseIP(ip)
				for _, cidr := range activeIPPools {
					if cidr.Contains(parsedIP) {
						found = true
						break
					}
				}
				if !found {
					if c.showIPs {
						for _, owner := range owners {
							fmt.Printf("  %s in use by %v is not in any active IP pool.\n", ip, owner.FriendlyName)
						}
					}
					nonCalicoIPs = append(nonCalicoIPs, ip)
					continue
				}
				if c.showIPs {
					for _, owner := range owners {
						fmt.Printf("  %s in use by %v and in active IPAM pool but has no IPAM allocation.\n", ip, owner.FriendlyName)
					}
				}
				inUseButNotAllocatedIPs = append(inUseButNotAllocatedIPs, ip)
			}
		}
		fmt.Printf("Found %d in-use IPs that are not in active IP pools.\n", len(nonCalicoIPs))
		fmt.Printf("Found %d in-use IPs that are in active IP pools but have no corresponding IPAM allocation.\n",
			len(inUseButNotAllocatedIPs))
	}

	return nil
}

func getWEPIPs(w apiv3.WorkloadEndpoint) ([]string, error) {
	var ips []string
	for _, a := range w.Spec.IPNetworks {
		ip, err := normaliseIP(a)
		if err != nil {
			return nil, fmt.Errorf("failed to parse IP (%s) of workload %s/%s: %w",
				a, w.Namespace, w.Name, err)
		}
		ips = append(ips, ip)
	}
	return ips, nil
}

func (c *IPAMChecker) recordAllocation(b *model.AllocationBlock, ord int) {
	ip := b.OrdinalToIP(ord).String()

	c.allocations[ip] = append(c.allocations[ip], allocation{
		Block:   b,
		Ordinal: ord,
	})

	attrIdx := *b.Allocations[ord]
	if len(b.Attributes) > attrIdx {
		attrs := b.Attributes[attrIdx]
		if attrs.AttrPrimary != nil && *attrs.AttrPrimary == ipam.WindowsReservedHandle {
			c.recordInUseIP(ip, b, "Reserved for Windows")
		}
	}
}

func (c *IPAMChecker) recordInUseIP(ip string, referrer interface{}, friendlyName string) {
	c.inUseIPs[ip] = append(c.inUseIPs[ip], ownerRecord{
		FriendlyName: friendlyName,
		Resource:     referrer,
	})
}

func getNodeIPs(n apiv3.Node) ([]string, error) {
	var ips []string
	if n.Spec.IPv4VXLANTunnelAddr != "" {
		ip, err := normaliseIP(n.Spec.IPv4VXLANTunnelAddr)
		if err != nil {
			return nil, fmt.Errorf("failed to parse IPv4VXLANTunnelAddr (%s) of node %s: %w",
				n.Spec.IPv4VXLANTunnelAddr, n.Name, err)
		}
		ips = append(ips, ip)
	}
	if n.Spec.Wireguard != nil && n.Spec.Wireguard.InterfaceIPv4Address != "" {
		ip, err := normaliseIP(n.Spec.Wireguard.InterfaceIPv4Address)
		if err != nil {
			return nil, fmt.Errorf("failed to parse Wireguard.InterfaceIPv4Address (%s) of node %s: %w",
				n.Spec.Wireguard.InterfaceIPv4Address, n.Name, err)
		}
		ips = append(ips, ip)
	}
	if n.Spec.BGP != nil && n.Spec.BGP.IPv4IPIPTunnelAddr != "" {
		ip, err := normaliseIP(n.Spec.BGP.IPv4IPIPTunnelAddr)
		if err != nil {
			return nil, fmt.Errorf("failed to parse IPv4IPIPTunnelAddr (%s) of node %s: %w",
				n.Spec.BGP.IPv4IPIPTunnelAddr, n.Name, err)
		}
		ips = append(ips, ip)
	}
	return ips, nil
}

func normaliseIP(addr string) (string, error) {
	ip, _, err := cnet.ParseCIDROrIP(addr)
	if err != nil {
		return "", err
	}
	return ip.String(), nil
}

type allocation struct {
	Block   *model.AllocationBlock
	Ordinal int
}

type ownerRecord struct {
	FriendlyName string
	Resource     interface{}
}
