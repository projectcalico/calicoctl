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

// TODO
// Better error handling
// Distinguish between deleted updates and other failures
// Copyright stuff related to k8s
// Windows/Linus newlines etc.
// Need to verify that user is not adding new entry or changing resource identifiers
// CreateResourcesFromBytes needs to be converted to slice ... this indicates a bug
//   in the CreateResourcesFromBytes which must be returning structs rather than pointers.

package commands

import (
	"bufio"
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	log "github.com/Sirupsen/logrus"
	"github.com/docopt/docopt-go"
	"github.com/projectcalico/calicoctl/calicoctl/commands/constants"

	"github.com/projectcalico/calicoctl/calicoctl/k8s-utils/editor"
	"github.com/projectcalico/calicoctl/calicoctl/resourcemgr"
	"github.com/projectcalico/libcalico-go/lib/api/unversioned"
)

func Edit(args []string) {
	doc := constants.DatastoreIntro + `Usage:
  calicoctl edit ([--scope=<SCOPE>] [--node=<NODE>] [--orchestrator=<ORCH>]
                  [--workload=<WORKLOAD>] (<KIND> [<NAME>]) |
                  --filename=<FILENAME>)
                 [--output=<OUTPUT>] [--config=<CONFIG>]

Examples:
  # Edit all policy in YAML format.
  calicoctl edit policy

  # Edit a specific policy in JSON format
  calicoctl edit -o json policy my-policy-1

  # Use an alternative editor
  CALICOCTL_EDITOR="nano" calicoctl edit policy

Options:
  -h --help                    Show this screen.
  -f --filename=<FILENAME>     Filename to use to get the resource.  If set to
                               "-" loads from stdin.
  -o --output=<OUTPUT FORMAT>  Output format.  One of: yaml, json.
                               [Default: yaml]
  -n --node=<NODE>             The node (this may be the hostname of the
                               compute server if your installation does not
                               explicitly set the names of each Calico node).
     --orchestrator=<ORCH>     The orchestrator (valid for workload endpoints).
     --workload=<WORKLOAD>     The workload (valid for workload endpoints).
     --scope=<SCOPE>           The scope of the resource type.  One of global,
                               node.  This is only valid for BGP peers and is
                               used to indicate whether the peer is a global
                               peer or node-specific.
  -c --config=<CONFIG>         Path to the file containing connection
                               configuration in YAML or JSON format.
                               [default: /etc/calico/calicoctl.cfg]

Description:
  The edit command is used to edit a set of resources that have been specified
  on the command line or through the specified file.  JSON and YAML formats are
  accepted for file and stdin format.

  Valid resource types are node, bgpPeer, hostEndpoint, workloadEndpoint,
  ipPool, policy and profile.  The <TYPE> is case insensitive and may be
  pluralized.

  Attempting to edit resources that do not exist is not possible.  Primary
  identifiers for the resources may not be changed in an edit.

  When editing resources by type, only a single type may be specified at a
  time.  The name and other identifiers (hostname, scope) are optional, and are
  wildcarded when omitted. Thus if you specify no identifiers at all (other
  than type), then all configured resources of the requested type will be
  returned.
`
	parsedArgs, err := docopt.Parse(doc, args, true, "", false, false)
	if err != nil {
		fmt.Printf("Invalid option: 'calicoctl %s'. Use flag '--help' to read about a specific subcommand.\n", strings.Join(args, " "))
		os.Exit(1)
	}
	if len(parsedArgs) == 0 {
		return
	}

	var (
		ext       string
		rp        resourcePrinter
		file      string
		resources []unversioned.Resource
		nb        []byte
	)
	output := parsedArgs["--output"].(string)
	switch output {
	case "yaml":
		ext = ".yaml"
		rp = resourcePrinterYAML{}
	case "json":
		ext = ".json"
		rp = resourcePrinterJSON{}
	default:
		fmt.Printf("unrecognized output format '%s'", output)
		os.Exit(1)
	}

	// Get the current results.
	results := executeConfigCommand(parsedArgs, actionList)
	log.Infof("results: %+v", results)

	if results.fileInvalid {
		fmt.Printf("Failed to execute command: %v\n", results.err)
		os.Exit(1)
	} else if results.err != nil {
		fmt.Printf("Failed to get resources: %v\n", results.err)
		os.Exit(1)
	} else if len(results.resources) == 0 {
		fmt.Println("Failed to find any matching resources.")
		os.Exit(1)
	}

	// Use the resource print to output to a buffer.
	buf := &bytes.Buffer{}
	if err = rp.write(buf, nil, results.resources); err != nil {
		fmt.Printf("Error outputing resources to file: %v\n", err)
		os.Exit(1)
	}
	b := buf.Bytes()

	// Create a new editor.
	edit := editor.NewDefaultEditor([]string{"CALICOCTL_EDITOR", "EDITOR"})
	for {
		// Add a comment to the top of the file describing the process
		// and any errors that previously occurred.
		b = addComment(b, err)
		buf = bytes.NewBuffer(b)
		nb, file, err = edit.LaunchTempFile(fmt.Sprintf("%s-edit-", filepath.Base(os.Args[0])), ext, buf)
		if err != nil {
			fmt.Printf("Unable to launch editor: %v\n", err)
			os.Exit(1)
		}

		// Remove the file since we'll open a new one if we need to.
		os.Remove(file)

		// If the user exited without changing anything then just exit.
		if bytes.Compare(b, nb) == 0 {
			fmt.Println("No changes made to file.  Exiting.")
			os.Exit(1)
		}

		// Remove the comment from the top of the file before parsing,
		// if the file is unchanged just exit.
		b = removeComment(nb)

		// Convert the file into a set of resources.  If this succeeds
		// then it passes validation, so exit this loop.
		resources, err = resourcemgr.CreateResourcesFromBytes(b)
		if err == nil {
			break
		}

		log.WithError(err).Debug("Failed validation, re-enter editor.")
	}

	ac := actionConfig{
		client: results.client,
		action: actionUpdate,
	}

	// Data edited and parsed.  Apply the changes - any errors now and we
	// exit.
	resources = convertToSliceOfResources(resources)
	failed := []unversioned.Resource{}
	for _, resource := range resources {
		if _, err = executeResourceAction(ac, resource); err != nil {
			failed = append(failed, resource)
		}
	}
	if len(failed) == 0 {
		fmt.Printf("Successfully updated %d resources.\n", len(resources))
	} else {
		if len(failed) == len(resources) {
			fmt.Printf("Failed to update any resource, last error: %s\n", err)
		} else {
			fmt.Printf("Failed to update %d/%d resources, last error: %s\n",
				len(failed), len(resources), err)
		}

		f, err := os.Create(file)
		if err == nil {
			err = rp.write(f, results.client, failed)
			f.Close()
			if err == nil {
				fmt.Printf("\nFailed resources written to file: %s\n", file)
			} else {
				os.Remove(file)
			}
		}
	}
}

// removeComment removes comments starting with ## from the file.
func removeComment(b []byte) []byte {
	nb := bytes.Buffer{}
	scanner := bufio.NewScanner(bytes.NewBuffer(b))
	for scanner.Scan() {
		// Skip lines starting with ##
		line := scanner.Bytes()
		if len(line) > 2 && line[0] == '#' && line[1] == '#' {
			continue
		}
		nb.Write(line)
		nb.Write(CR)
	}
	return nb.Bytes()
}

// addComment adds a help comment and current error message to the top of the file.
func addComment(b []byte, err error) []byte {
	nb := bytes.Buffer{}
	nb.WriteString("## Edit the contents of the file and save to apply the changes.\n")
	nb.WriteString("## Errors when applying will be displayed below in this comment, the changes\n")
	nb.WriteString("## may be re-applied.\n")
	if err != nil {
		nb.WriteString("##\n")
		errString := fmt.Sprint(err)
		for _, line := range strings.Split(errString, "\n") {
			nb.WriteString("## ")
			nb.WriteString(line)
			nb.WriteString("\n")
		}
	}
	nb.WriteString("##\n")

	nb.Write(b)
	return nb.Bytes()
}
