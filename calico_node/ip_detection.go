package main

import (
	"fmt"
	"net"
	"regexp"
	"strings"
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

				ip := strings.Split(addr.String(), "/")[0]
				valid_ip := net.ParseIP(ip)

				if valid_ip.To4() != nil{
					ips = append(ips, ip)
				}
					
				}
			}
		}
	return ips, err
}