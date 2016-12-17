package autodetection

import (
	"fmt"
	"net"
	"regexp"
	"strings"
	log "github.com/Sirupsen/logrus"
)

// GetValidInterfaces returns a list of all interfaces which do not match
// a regex from ignoreInterfaces

func GetValidInterfaces(ignoreInterfaces []string) ([]net.Interface, error) {
	valid_ifaces := []net.Interface{}
	ifaces, err := net.Interfaces()
	if err != nil {
		log.Warnf("Interfaces unavailable: %v", err)
		return nil, err
	}

	for _, iface := range ifaces {
		if len(ignoreInterfaces) == 0 {
			valid_ifaces = append(valid_ifaces, iface)
		} else {
		 	for _, r := range ignoreInterfaces {
		 		regex, err := regexp.Compile(r)
		 		if err != nil {
		 			log.Warnf("Cannot compile regex: %v", err)
					return nil, err
				}
		 	    if !regex.MatchString(iface.Name) {
					valid_ifaces = append(valid_ifaces, iface)
					break
				}
			}
		}
	}
	return valid_ifaces, nil
}

// Returns a string array of all valid IPs for a given interface.
// 4 returns ipv4s, 6 returns ipv6s
func GetIPsFromIface(iface net.Interface, ip_type int) ([]string, []string, error) {
	ips := []string{}
	addrs, err := iface.Addrs()
	if err != nil {
		log.Warnf("Cannot get interface address(es): %v", err)
		return nil, err
	}
	
	for _, addr := range addrs {
		ip := strings.Split(addr.String(), "/")[0]
		valid_ip := net.ParseIP(ip)
		if valid_ip.To4() != nil && ip_type == 4{
			ips = append(ips, ip)
		} else if valid_ip != nil && ip_type == 6{
			ips = append(ips, ip)
		}
	return ips, nil
}