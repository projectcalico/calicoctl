package allocateIPIPAddr

import (
	log "github.com/Sirupsen/logrus"

	"github.com/projectcalico/libcalico-go/lib/api"
	"github.com/projectcalico/libcalico-go/lib/client"
	"debug/pe"
)

func allocateIPIPAddr(client *client.Client, string nodename) {
	meta := api.IPPoolMetadata{}
	ipPoolList, err := client.IPPools().List(meta)
	if err != nil {
		log.Warnf("error retrieving pools: %s", err)
	}
    ipv4Pools := getIPv4Pools(ipPoolList.Items)
    enabledPools := getIPIPEnabledPools(ipv4Pools)
    if len(enabledPools) > 0 {
        ensureHostTunnelAddress(ipv4Pools, enabledPools, client, nodename)
    } else {
        removeHostTunnelAddr(client, nodename)
    }
}

func ensureHostTunnelAddress(ipv4Pools, enabledPools []api.IPPool, client *client.Client, string nodename){
    cnf = client.Config()
    ipAddr, err := cnf.GetNodeIPIPTunnelAddress(nodename)
    if err != nil {
        panic(fmt.Sprintf("Could not retrieve IPIP tunnel address: %s", err))
    }
    if ipAddr != nil {
        pool, _ := findPool(ipAddr, ipv4Pools)
        if pool != nil {
            if pool.Spec.IPPoolSpec.IPIP == false {
                _, err := client.IPAM().ReleaseIPs([]*net.IP{ipAddr})
                if err != nil {
                    panic(fmt.Sprintf("Error releasing non IPIP address: %s", err))
                }
                ipAddr = nil
            }
        } else {
            ipAddr = nil
        }
    }
    if ipAddr == nil {
        assignHostTunnelAddr(enabledPools, client, nodename)
    }
}


func removeHostTunnelAddr(client *client.Client, nodename string) {
    ipAddr, err := cnf.GetNodeIPIPTunnelAddress(nodename)
    if err != nil {
        panic(fmt.Sprintf("Could not retrieve IPIP tunnel address for cleanup: %s", err))
    }
    if ipAddr != nil {
        _, err := client.IPAM().ReleaseIPs([]*net.IP{ipAddr})
        if err != nil {
            panic(fmt.Sprintf("Error releasing address: %s", err))
        }
    }
    ipam := client.IPAM()
    err := ipam.UnsetFelixConfig("IpInIpTunnelAddr", nodename)
}

func assignHostTunnelAddr(ipipPools []api.IPPool, *client.Client, nodename string) {
    args := AutoAssignArgs{Num4: 1, Num6:0, HandleID: nil, Attrs: nil, Hostname: nodename, IPv4Pools: ipipPools}
    ipam := client.IPAM()
    ipv4Addrs, _, err := ipam.AutoAssign(args)
    if err != nil {
        panic(fmt.Sprintf("Could not autoassign host tunnel address: %s", err))
    }
    if len(ipv4Addrs) > 0 {
        config := client.Config()
        config.SetFelixConfig("IpInIpTunnelAddr", nodename, ipv4Addrs[0].String())
    } else {
        panic(fmt.Sprintf("Failed to allocate an IP address from an IPIP-enabled pool 
for the host's IPIP tunnel device.  Pools are likely exhausted."))
    } 
}

func findPool(ipAddr *net.IP, ipv4Pools []api.IPPool) (net.IPNet, error) {
    for _, p in range ipv4Pools {
        poolIP := p.IPPoolMetadata.CIDR.String()
        if strings.HasPrefix(poolIP, ipAddr) {
            return p, nil
        }
    }
    return nil, nil
}

func getIPv4Pools(ipPools []api.IPPool) {
    result := []api.IPPool{}
    for _, ipPool in ipPoolList.Items {
        if ipPool.Metadata.CIDR.version == 4 {
            append(result, ipPool)
        }
    }
    return result
}

func getIPIPEnabledPools(ipPools []api.IPPool) {
    result := []api.IPPool{}
    for _, ipPool in ipPoolList.Items {
        if ipPool.Spec.IPIP.enabled == true {
            append(result, ipPool)
        }
    }
    return result
}

