package ip_detection

import (
	"errors"
	"fmt"
	"net"
	"regexp"
)

func detectIPs(ignoreInterfaces []string) ([]string, error) {

	ips := []string{}
	ifaces, err := net.Interfaces()

	for _, iface := range ifaces {

		valid_ip := true

		// Check each interface name against 
		// list of interfaces to ignore.
		for _, v := range ignoreInterfaces {
			regex, err := regexp.Compile(v)

			if err != nil {
				continue
			}

			if regex.MatchString(iface.Name) {
				valid_ip = false
			}
		}

		if valid_ip == true {
			addrs, err := iface.Addrs()

			if err != nil {
				continue
			}
			
			for _, addr := range addrs {
				ips = append(ips, addr.String())
					
				}
			}
		}
	return ips, err
}