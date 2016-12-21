package autodetection

import (
	"fmt"
	"net"
	"regexp"
	"strings"

	log "github.com/Sirupsen/logrus"
	cnet "github.com/projectcalico/libcalico-go/lib/net"
)

// Interface contains details about an interface on the host.
type Interface struct {
	Name  string
	Addrs []Addr
}

// Addr contains details about a specific interface address.  The IPAddress will
// always be assigned, but the network may not.
type Addr struct {
	IPAddress *cnet.IP
	IPNetwork *cnet.IPNet
}

func (a Addr) String() string {
	return fmt.Sprintf("Addr(IP=%s,Net=%s)", a.IPAddress, a.IPNetwork)
}

// GetInterfaces returns a list of all interfaces, skipping any interfaces whose
// name matches any of the exclusion list regexes, and including those on the
// inclusion list.
func GetInterfaces(includeRegexes []string, excludeRegexes []string, version int) ([]Interface, error) {
	// Create a single regex to perform the interface check.
	netIfaces, err := net.Interfaces()
	if err != nil {
		log.Warnf("Interfaces unavailable: %v", err)
		return nil, err
	}

	var filteredIfaces []Interface
	var includeRegexp *regexp.Regexp
	var excludeRegexp *regexp.Regexp
	if len(includeRegexes) > 0 {
		includeRegexp = regexp.MustCompile("(" + strings.Join(includeRegexes, ")|(") + ")")
	}
	if len(excludeRegexes) > 0 {
		excludeRegexp = regexp.MustCompile("(" + strings.Join(excludeRegexes, ")|(") + ")")
	}
	for _, iface := range netIfaces {
		include := (includeRegexp == nil) || includeRegexp.MatchString(iface.Name)
		exclude := (excludeRegexp != nil) && excludeRegexp.MatchString(iface.Name)
		if include && !exclude {
			if i, err := convertInterface(&iface, version); err == nil {
				filteredIfaces = append(filteredIfaces, *i)
			}
		}
	}
	return filteredIfaces, nil
}

// Convert a net.Interface to our Interface type (which has converted Address
// types).
func convertInterface(i *net.Interface, version int) (*Interface, error) {
	log.WithField("Interface", i.Name).Info("Query interface addresses")
	addrs, err := i.Addrs()
	if err != nil {
		log.Warnf("Cannot get interface address(es): %v", err)
		return nil, err
	}

	iface := &Interface{Name: i.Name}
	for _, addr := range addrs {
		ia := Addr{}

		addrStr := addr.String()
		if strings.Contains(addrStr, "/") {
			log.Debug("Parsing as CIDR")
			ia.IPAddress, ia.IPNetwork, _ = cnet.ParseCIDR(addrStr)
		} else {
			log.Debug("Parsing as IP")
			ia.IPAddress = &cnet.IP{}
			if err = ia.IPAddress.UnmarshalText([]byte(addrStr)); err != nil {
				ia.IPAddress = nil
			}
		}

		if ia.IPAddress == nil {
			log.WithField("Address", addrStr).Info("Unable to parse IP address")
			continue
		}

		if ia.IPAddress.Version() == version {
			log.WithField("Addr", ia).Info("Storing IP and network in interface")
			iface.Addrs = append(iface.Addrs, ia)
		}
	}

	return iface, nil
}
