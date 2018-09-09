// Copyright (c) 2016-2017 Tigera, Inc. All rights reserved.

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

package commands

import (
	"context"
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"github.com/projectcalico/calicoctl/calicoctl/commands/clientmgr"
	"github.com/projectcalico/calicoctl/calicoctl/commands/constants"
	"github.com/projectcalico/libcalico-go/lib/options"
)

var (
	VERSION                  string
	BUILD_DATE, GIT_REVISION string // unused
	cf                       = constants.DefaultConfigPath
)

func init() {
	VersionCommand.Flags().StringVarP(&cf, "config", "c", constants.DefaultConfigPath, "Path to the file containing connection configuration in YAML or JSON format.")
}

var VersionCommand = &cobra.Command{
	Use:   "version",
	Short: "Display the version of calicoctl",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Client Version:   ", VERSION)

		// Load the client config and connect.
		client, err := clientmgr.NewClient(cf)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		ctx := context.Background()
		ci, err := client.ClusterInformation().Get(ctx, "default", options.GetOptions{})
		if err != nil {
			fmt.Println("Unable to retrieve Cluster Version or Type: ", err)
			os.Exit(1)
		}

		v := ci.Spec.CalicoVersion
		if v == "" {
			v = "unknown"
		}
		t := ci.Spec.ClusterType
		if t == "" {
			t = "unknown"
		}

		fmt.Println("Cluster Version:  ", v)
		fmt.Println("Cluster Type:     ", t)
	},
}
