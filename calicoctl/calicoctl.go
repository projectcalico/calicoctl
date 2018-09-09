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

package main

import (
	"fmt"
	"os"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"

	"github.com/projectcalico/calicoctl/calicoctl/commands"
)

var (
	rootCmd = &cobra.Command{
		Use:   "calicoctl",
		Short: "manage Calico resources",
		Long: `The calicoctl command line tool is used to manage 
Calico network and security policy, to view and manage 
endpoint configuration, and to manage a Calico node instance.`,
		Version: commands.VERSION,
	}
)

func main() {
	rootCmd.AddCommand(commands.CreateCommand)
	rootCmd.AddCommand(commands.ReplaceCommand)
	rootCmd.AddCommand(commands.ApplyCommand)
	rootCmd.AddCommand(commands.DeleteCommand)
	rootCmd.AddCommand(commands.GetCommand)
	rootCmd.AddCommand(commands.ConvertCommand)
	rootCmd.AddCommand(commands.VersionCommand)
	rootCmd.AddCommand(commands.NodeCommand)
	rootCmd.AddCommand(commands.IPAMCommand)

	// handle log level option
	logLevel := rootCmd.Flags().StringP(
		"log-level", "l", "panic",
		"Set the log level (one of panic, fatal, error, warn, info, debug")
	parsedLogLevel, err := log.ParseLevel(*logLevel)
	if err != nil {
		fmt.Printf("Unknown log level: %s, expected one of: \n"+
			"panic, fatal, error, warn, info, debug.\n", logLevel)
		os.Exit(1)
	} else {
		log.SetLevel(parsedLogLevel)
		log.Infof("Log level set to %v", parsedLogLevel)
	}

	// Execute command
	rootCmd.Execute()
	return
}
