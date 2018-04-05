// Copyright (c) 2016 Tigera, Inc. All rights reserved.

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

package node

import (
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/projectcalico/libcalico-go/bird"

	"github.com/docopt/docopt-go"
	gops "github.com/mitchellh/go-ps"
	"github.com/olekukonko/tablewriter"
	gobgp "github.com/osrg/gobgp/client"
	"github.com/osrg/gobgp/packet/bgp"
	log "github.com/sirupsen/logrus"
)

// Status prints status of the node and returns error (if any)
func Status(args []string) {
	doc := `Usage:
  calicoctl node status

Options:
  -h --help                 Show this screen.

Description:
  Check the status of the Calico node instance.  This includes the status and
  uptime of the node instance, and BGP peering states.
`

	parsedArgs, err := docopt.Parse(doc, args, true, "", false, false)
	if err != nil {
		fmt.Printf("Invalid option: 'calicoctl %s'. Use flag '--help' to read about a specific subcommand.\n", strings.Join(args, " "))
		os.Exit(1)
	}
	if len(parsedArgs) == 0 {
		return
	}

	// Must run this command as root to be able to connect to BIRD sockets
	enforceRoot()

	// Go through running processes and check if `calico-felix` processes is not running
	processes, err := gops.Processes()
	if err != nil {
		fmt.Println(err)
	}
	if !psContains("calico-felix", processes) {
		// Return and print message if calico-node is not running
		fmt.Printf("Calico process is not running.\n")
		os.Exit(1)
	}

	fmt.Printf("Calico process is running.\n")

	if psContains("bird", processes) || psContains("bird6", processes) {
		// Check if birdv4 process is running, print the BGP peer table if it is, else print a warning
		if psContains("bird", processes) {
			printBIRDPeers("4")
		} else {
			fmt.Printf("\nINFO: BIRDv4 process: 'bird' is not running.\n")
		}
		// Check if birdv6 process is running, print the BGP peer table if it is, else print a warning
		if psContains("bird6", processes) {
			printBIRDPeers("6")
		} else {
			fmt.Printf("\nINFO: BIRDv6 process: 'bird6' is not running.\n")
		}
	} else if psContains("calico-bgp-daemon", processes) {
		printGoBGPPeers("4")
		printGoBGPPeers("6")
	} else {
		fmt.Printf("\nNone of the BGP backend processes (BIRD or GoBGP) are running.\n")
	}

	// Have to manually enter an empty line because the table print
	// library prints the last line, so can't insert a '\n' there
	fmt.Println()
}

func psContains(proc string, procList []gops.Process) bool {
	if len(proc) > 15 {
		// go-ps returns executable name which is truncated to 15 characters.
		// Some work is proceeding to fix this. https://github.com/mitchellh/go-ps/pull/14
		// Until this get fixed, truncate proc to size 15.
		proc = proc[:15]
	}
	for _, p := range procList {
		if p.Executable() == proc {
			return true
		}
	}
	return false
}

// Check for Word_<IP> where every octate is seperated by "_", regardless of IP protocols
// Example match: "Mesh_192_168_56_101" or "Mesh_fd80_24e2_f998_72d7__2"
var bgpPeerRegex = regexp.MustCompile(`^(Global|Node|Mesh)_(.+)$`)

// Mapping the BIRD/GoBGP type extracted from the peer name to the display type.
var bgpTypeMap = map[string]string{
	"Global": "global",
	"Mesh":   "node-to-node mesh",
	"Node":   "node specific",
}

// Timeout for querying BIRD
var birdTimeOut = 2 * time.Second

// Expected BIRD protocol table columns
var birdExpectedHeadings = []string{"name", "proto", "table", "state", "since", "info"}

// printBIRDPeers queries BIRD and displays the local peers in table format.
func printBIRDPeers(ipv string) {
	fmt.Printf("\nIPv%s BGP status\n", ipv)
	peers, err := bird.GetPeers(ipv)
	if err != nil {
		fmt.Printf("Error getting peers: %v", err)
		return
	}

	// If no peers were returned then just print a message.
	if len(peers) == 0 {
		fmt.Printf("No IPv%s peers found.\n", ipv)
		return
	}

	printPeers(peers)
}

// printGoBGPPeers queries GoBGP and displays the local peers in table format.
func printGoBGPPeers(ipv string) {
	client, err := gobgp.New("")
	if err != nil {
		fmt.Printf("Error creating gobgp client: %s\n", err)
		os.Exit(1)
	}
	defer client.Close()

	afi := bgp.AFI_IP
	if ipv == "6" {
		afi = bgp.AFI_IP6
	}

	fmt.Printf("\nIPv%s BGP status\n", ipv)

	neighbors, err := client.ListNeighborByTransport(afi)
	if err != nil {
		fmt.Printf("Error retrieving neighbor info: %s\n", err)
		os.Exit(1)
	}

	formatTimedelta := func(d int64) string {
		u := uint64(d)
		neg := d < 0
		if neg {
			u = -u
		}
		secs := u % 60
		u /= 60
		mins := u % 60
		u /= 60
		hours := u % 24
		days := u / 24

		if days == 0 {
			return fmt.Sprintf("%02d:%02d:%02d", hours, mins, secs)
		} else {
			return fmt.Sprintf("%dd ", days) + fmt.Sprintf("%02d:%02d:%02d", hours, mins, secs)
		}
	}

	now := time.Now()
	peers := make([]bird.BGPPeer, 0, len(neighbors))

	for _, n := range neighbors {
		ipString := n.Config.NeighborAddress
		description := n.Config.Description
		adminState := string(n.State.AdminState)
		sessionState := strings.Title(string(n.State.SessionState))

		timeStr := "never"
		if n.Timers.State.Uptime != 0 {
			t := int(n.Timers.State.Downtime)
			if sessionState == "Established" {
				t = int(n.Timers.State.Uptime)
			}
			timeStr = formatTimedelta(int64(now.Sub(time.Unix(int64(t), 0)).Seconds()))
		}

		sm := bgpPeerRegex.FindStringSubmatch(description)
		if len(sm) != 3 {
			log.Debugf("Not a valid line: peer name '%s' is not recognized", description)
			continue
		}
		var ok bool
		var typ string
		if typ, ok = bgpTypeMap[sm[1]]; !ok {
			log.Debugf("Not a valid line: peer type '%s' is not recognized", sm[1])
			continue
		}

		// TODO: stop hijacking bird's BGP Peer struct
		peers = append(peers, bird.BGPPeer{
			PeerIP:   ipString,
			PeerType: typ,
			State:    adminState,
			Since:    timeStr,
			BGPState: sessionState,
		})
	}

	// If no peers were returned then just print a message.
	if len(peers) == 0 {
		fmt.Printf("No IPv%s peers found.\n", ipv)
		return
	}

	// Finally, print the peers.
	printPeers(peers)
}

// printPeers prints out the slice of peers in table format.
func printPeers(peers []bird.BGPPeer) {
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"Peer address", "Peer type", "State", "Since", "Info"})

	for _, peer := range peers {
		info := peer.BGPState
		if peer.Info != "" {
			info += " " + peer.Info
		}
		row := []string{
			peer.PeerIP,
			peer.PeerType,
			peer.State,
			peer.Since,
			info,
		}
		table.Append(row)
	}

	table.Render()
}
