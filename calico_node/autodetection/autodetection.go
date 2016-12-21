package autodetection

import (
	"net"
	"regexp"
	"strings"

	log "github.com/Sirupsen/logrus"
)

// GetValidInterfaces returns a list of all interfaces which do not match
// a regex from ignoreInterfaces
func GetValidInterfaces(ignoreInterfaces []string) ([]net.Interface, error) {
	validIfaces := []net.Interface{}
	ifaces, err := net.Interfaces()
	if err != nil {
		log.Warnf("Interfaces unavailable: %v", err)
		return nil, err
	}

	if len(ignoreInterfaces) == 0 {
		return validIfaces, nil
	}

	for _, iface := range ifaces {
		for _, r := range ignoreInterfaces {
			regex, err := regexp.Compile(r)
			if err != nil {
				log.Warnf("Cannot compile regex: %v", err)
				return nil, err
			}
			if !regex.MatchString(iface.Name) {
				validIfaces = append(validIfaces, iface)
				break
			}
		}
	}
	return validIfaces, nil
}

// GetIPsFromIface returns a string array of all valid IPs for a given interface.
// 4 returns ipv4s, 6 returns ipv6s
func GetIPsFromIface(iface net.Interface, ipType int) ([]string, error) {
	ips := []string{}
	addrs, err := iface.Addrs()
	if err != nil {
		log.Warnf("Cannot get interface address(es): %v", err)
		return nil, err
	}

	for _, addr := range addrs {
		ip := strings.Split(addr.String(), "/")[0]
		validIP := net.ParseIP(ip)
		if validIP.To4() != nil && ipType == 4 {
			ips = append(ips, ip)
		} else if validIP != nil && ipType == 6 {
			ips = append(ips, ip)
		}
	}
	return ips, nil
}

// AutodetectIPv4 gets first valid ipv4 from valid interface.
func AutodetectIPv4(ignoreInterfaces []string) (string, error) {
	validIfaces, err := GetValidInterfaces(ignoreInterfaces)
	if err != nil {
		return "", err
	}
	for _, iface := range validIfaces {
		ipList, err := GetIPsFromIface(iface, 4)
		if err != nil {
			log.Warnf("Error detecting ipv4 address: %s", err)
		}
		if len(ipList) > 0 {
			return ipList[0], nil
		}
	}
	return "", nil
}
