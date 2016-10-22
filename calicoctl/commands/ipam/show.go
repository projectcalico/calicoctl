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

package ipam

import (
	"fmt"

	"github.com/projectcalico/calico-containers/calicoctl/commands/common"
	cnet "github.com/projectcalico/libcalico-go/lib/net"

	docopt "github.com/docopt/docopt-go"
)

// IPAM takes keyword with an IP address then calls the subcommands.
func Show(args []string) error {
	doc := common.DatastoreIntro + `Usage:
  calicoctl ipam show --ip=<IP>

Options:
  -h --help      Show this screen.
     --ip=<IP>   IP address

Description:
  The ipam show command prints information about a given IP address, such as special
  attributes defined for the IP or whether the IP has been reserved by a user of
  the Calico IP Address Manager.`

	parsedArgs, err := docopt.Parse(doc, args, true, "", false, false)
	if err != nil {
		return err
	}
	if len(parsedArgs) == 0 {
		return nil
	}

	// Create a new backend client from env vars.
	backendClient, err := common.NewClient("")
	if err != nil {
		fmt.Println(err)
	}

	ipamClient := backendClient.IPAM()
	passedIP := parsedArgs["--ip"].(string)
	ip := validateIP(passedIP)
	attr, err := ipamClient.GetAssignmentAttributes(cnet.IP{ip})

	// IP address is not assigned, this prints message like
	// `IP 192.168.71.1 is not assigned in block`. This is not exactly an error,
	// so not returning it to the caller.
	if err != nil {
		fmt.Println(err)
		return nil
	}

	// IP address is assigned with attributes.
	if len(attr) != 0 {
		fmt.Println(attr)
	} else {
		// IP address is assigned but attributes are not set.
		fmt.Printf("No attributes defined for IP %s\n", ip)
	}

	return nil
}
