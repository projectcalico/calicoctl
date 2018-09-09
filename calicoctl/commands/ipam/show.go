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
	"context"
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"github.com/projectcalico/calicoctl/calicoctl/commands/argutils"
	"github.com/projectcalico/calicoctl/calicoctl/commands/clientmgr"
)

func init() {
	ipamShowArgs = newIPAMArgs(ShowCommand.Flags())
	ShowCommand.MarkFlagRequired("ip")
}

var (
	ipamShowArgs ipamArgs
	ShowCommand  = &cobra.Command{
		Use:   "show",
		Short: "Show details of a Calico assigned IP address.",
		Long: `The ipam show command prints information about a given IP address, such as
special attributes defined for the IP or whether the IP has been reserved by
a user of the Calico IP Address Manager.`,
		Run: func(cmd *cobra.Command, args []string) {
			ctx := context.Background()

			// Create a new backend client from env vars.
			client, err := clientmgr.NewClient(*ipamShowArgs.config)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}

			ipamClient := client.IPAM()
			ip := argutils.ValidateIP(*ipamShowArgs.ip)
			attr, err := ipamClient.GetAssignmentAttributes(ctx, ip)

			// IP address is not assigned, this prints message like
			// `IP 192.168.71.1 is not assigned in block`. This is not exactly an error,
			// so not returning it to the caller.
			if err != nil {
				fmt.Println(err)
				return
			}

			// IP address is assigned with attributes.
			if len(attr) != 0 {
				fmt.Println(attr)
			} else {
				// IP address is assigned but attributes are not set.
				fmt.Printf("No attributes defined for IP %s\n", ip)
			}
		},
	}
)
