package allocateIPIPAddr

import (
	"fmt"
	"os"

	log "github.com/Sirupsen/logrus"

	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/client"
	"github.com/projectcalico/libcalico-go/lib/net"
)

// main sets the host's tunnel address to an IPIP-enabled address if
// there are any available, otherwise sets the tunnel to nil.
func main() {
	cfg, err := client.LoadClientConfig("")
	if err != nil {
		panic(fmt.Sprintf("Error loading config: %s", err))
	}
	c, err := client.New(*cfg)
	if err != nil {
		panic(fmt.Sprintf("Error creating client: %s", err))
	}
	nodename := os.Getenv("NODENAME")

	meta := api.IPPoolMetadata{}
	ipPoolList, err := c.IPPools().List(meta)
	if err != nil {
		log.Warnf("error retrieving pools: %s", err)
	}
	fmt.Println(ipPoolList)
	enabledPools := getIPIPEnabledPools(ipPoolList.Items)
	if len(enabledPools) > 0 {
		ensureHostTunnelAddress(enabledPools, c, nodename)
	} else {
		removeHostTunnelAddr(c, nodename)
	}
}

// ensureHostTunnelAddress that ensures the host
// has a valid IP address for its IPIP tunnel device.
// This must be an IP address claimed from one of the IPIP pools.
// Handles re-allocating the address if it finds an existing address
// that is not from an IPIP pool.
func ensureHostTunnelAddress(enabledPools []api.IPPool, c *client.Client, nodename string) {
	cnf := c.Config()
	fmt.Println(nodename)
	ipAddr, err := cnf.GetNodeIPIPTunnelAddress(nodename)
	if err != nil {
		panic(fmt.Sprintf("Could not retrieve IPIP tunnel address: %s", err))
	}
	if ipAddr != nil {
		pool, _ := findIPNet(ipAddr, enabledPools)
		if pool.String() == "" {
			ipsToRelease := []net.IP{*ipAddr}
			_, err := c.IPAM().ReleaseIPs(ipsToRelease)
			if err != nil {
				log.Warnf("Error releasing non IPIP address: %s", err)
				os.Exit(1)
			}
			ipAddr = nil
		}
	} else {
		assignHostTunnelAddr(enabledPools, c, nodename)
	}
}

// removeHostTunnelAddr removes any existing IP address for this
// host's IPIP tunnel device. Idempotent; does nothing if there is
// no IP assigned. Releases the IP from IPAM.
func removeHostTunnelAddr(client *client.Client, nodename string) {
	ipAddr, err := client.Config().GetNodeIPIPTunnelAddress(nodename)
	if err != nil {
		panic(fmt.Sprintf("Could not retrieve IPIP tunnel address for cleanup: %s", err))
	}
	if ipAddr != nil {
		_, err := client.IPAM().ReleaseIPs([]net.IP{*ipAddr})
		if err != nil {
			panic(fmt.Sprintf("Error releasing address: %s", err))
		}
	}
	cfg := client.Config()
	err = cfg.SetNodeIPIPTunnelAddress(nodename, nil)
}

// assignHostTunnelAddr claims an IPIP-enabled IP address from
// the first pool with some space. Stores the result in the host's
// config as its tunnel address. Exits on failure.
func assignHostTunnelAddr(ipipPools []api.IPPool, c *client.Client, nodename string) {
	var ipNets []net.IPNet
	for _, p := range ipipPools {
		ipNets = append(ipNets, p.Metadata.CIDR)
	}
	args := client.AutoAssignArgs{Num4: 1, Num6: 0, HandleID: nil, Attrs: nil, Hostname: nodename, IPv4Pools: ipNets}
	ipam := c.IPAM()
	ipv4Addrs, _, err := ipam.AutoAssign(args)
	if err != nil {
		panic(fmt.Sprintf("Could not autoassign host tunnel address: %s", err))
	}
	fmt.Println("IPV4 ADDRESSES")
	fmt.Println(ipv4Addrs)
	if len(ipv4Addrs) > 0 {
		cfg := c.Config()
		cfg.SetNodeIPIPTunnelAddress(nodename, &ipv4Addrs[0])
	} else {
		panic(fmt.Sprintf("Failed to allocate an IP address from an IPIP-enabled pool for the host's IPIP tunnel device.  Pools are likely exhausted."))
	}
}

// findPool returns the IPNet containing the given IP.
func findIPNet(ipAddr *net.IP, ipPools []api.IPPool) (net.IPNet, error) {
	for _, pool := range ipPools {
		poolIPNet := pool.Metadata.CIDR
		if poolIPNet.Contains(ipAddr.IP) {
			return poolIPNet, nil
		}
	}
	return net.IPNet{}, nil
}

// getIPIPEnabledPools returns all IPIP enabled pools.
func getIPIPEnabledPools(ipPools []api.IPPool) []api.IPPool {
	var result []api.IPPool
	for _, ipPool := range ipPools {
		if ipPool.Spec.IPIP != nil && ipPool.Spec.IPIP.Enabled {
			result = append(result, ipPool)
		}
	}
	return result
}
