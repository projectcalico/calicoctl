// Copyright (c) 2020 Tigera, Inc. All rights reserved.

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
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"strings"

	"github.com/docopt/docopt-go"
	log "github.com/sirupsen/logrus"

	"github.com/projectcalico/calicoctl/calicoctl/commands/clientmgr"
	"github.com/projectcalico/calicoctl/calicoctl/commands/constants"
	"github.com/projectcalico/libcalico-go/lib/apiconfig"
	apiv3 "github.com/projectcalico/libcalico-go/lib/apis/v3"
	client "github.com/projectcalico/libcalico-go/lib/clientv3"
	"github.com/projectcalico/libcalico-go/lib/options"
	"k8s.io/apimachinery/pkg/api/meta"
)

func Import(args []string) error {
	doc := `Usage:
  calicoctl import --filename=<FILENAME> [--config=<CONFIG>]

Options:
  -h --help                 Show this screen.
  -f --filename=<FILENAME>  Filename to use to import resources.  If set to
                            "-" loads from stdin.
  -c --config=<CONFIG>      Path to the file containing connection
                            configuration in YAML or JSON format.
                            [default: ` + constants.DefaultConfigPath + `]

Description:
  Import the contents of the etcdv3 datastore from the file created by the
  export command.
`

	parsedArgs, err := docopt.Parse(doc, args, true, "", false, false)
	if err != nil {
		return fmt.Errorf("Invalid option: 'calicoctl %s'. Use flag '--help' to read about a specific subcommand.", strings.Join(args, " "))
	}
	if len(parsedArgs) == 0 {
		return nil
	}

	// Get the backend client for updating cluster info and migrating IPAM.
	cf := parsedArgs["--config"].(string)
	client, err := clientmgr.NewClient(cf)
	if err != nil {
		return err
	}

	// Check that the datastore configured datastore is kubernetes
	cfg, err := clientmgr.LoadClientConfig(cf)
	if err != nil {
		log.Info("Error loading config")
		return err
	}

	if cfg.Spec.DatastoreType != apiconfig.Kubernetes {
		return fmt.Errorf("Invalid datastore type: %s to import to for datastore migration. Datastore type must be kubernetes", cfg.Spec.DatastoreType)
	}

	// TODO: Attempt to import the CRDs here

	// TODO: On failure, print instructions on how to cleanse datastore
	/*
		err = checkCalicoResourcesNotExist(parsedArgs)
		if err != nil {
			return fmt.Errorf("Datastore already has Calico resources: %s. INSERT INSTRUCTIONS TO DELETE", err)
		}
	*/

	// Ensure that the cluster info resource is initialized.
	ctx := context.Background()
	if err := client.EnsureInitialized(ctx, "", ""); err != nil {
		return fmt.Errorf("Unable to initialize cluster information for the datastore migration: %s", err)
	}
	// TODO: Need to ensure the datastore is locked here.

	// Split file into v3 API, ClusterGUID, and IPAM components
	filename := parsedArgs["--filename"].(string)
	v3Yaml, clusterInfoJson, ipamJson, err := splitImportFile(filename)
	if err != nil {
		return fmt.Errorf("Error while reading migration file: %s\n", err)
	}

	// Apply v3 API resources
	err = updateV3Resources(v3Yaml)
	if err != nil {
		return fmt.Errorf("Failed to import v3 resources: %s\n", err)
	}

	// Create the cluster info resource. This should not exist since calico-node was only writing to the etcd datastore.
	err = updateClusterInfo(ctx, client, clusterInfoJson)
	if err != nil {
		return fmt.Errorf("Failed to update cluster information: %s", err)
	}

	// Import IPAM components
	fmt.Print("Importing IPAM resources\n")
	ipam := NewMigrateIPAM(client)
	err = json.Unmarshal(ipamJson, ipam)
	if err != nil {
		return fmt.Errorf("Failed to read IPAM resources: %s\n", err)
	}
	results := ipam.PushToDatastore()

	// Handle the IPAM results
	if results.numHandled == 0 {
		if results.numResources == 0 {
			return fmt.Errorf("No IPAM resources specified in file")
		} else {
			return fmt.Errorf("Failed to import any IPAM resources: %v", results.resErrs)
		}
	} else if len(results.resErrs) == 0 {
		fmt.Printf("Successfully applied %d IPAM resource(s)\n", results.numHandled)
	} else {
		if results.numHandled != 0 && len(results.resErrs) > 0 {
			fmt.Printf("Partial success: ")
			fmt.Printf("applied the first %d out of %d resources:\n", results.numHandled, results.numResources)
		}
		return fmt.Errorf("Hit error(s): %v", results.resErrs)
	}

	fmt.Print("Datastore information successfully imported. To complete the datastore migration, run `calicoctl unlock` and modify your calico configuration to match the kubenretes datastore.\n")

	return nil
}

func splitImportFile(filename string) ([]byte, []byte, []byte, error) {
	// Get the appropriate file to read from
	fname := filename
	if filename == "-" {
		fname = os.Stdin.Name()
	}

	b, err := ioutil.ReadFile(fname)
	if err != nil {
		return []byte{}, []byte{}, []byte{}, err
	}

	split := bytes.Split(b, []byte("===\n"))
	if len(split) != 3 {
		return []byte{}, []byte{}, []byte{}, fmt.Errorf("Imported file: %s is improperly formatted. Try recreating with 'calicoctl export'", fname)
	}

	// First chunk should be the v3 resource YAML.
	// Second chunk should give the cluster info resource.
	// Last chunk should be the IPAM JSON.
	return split[0], split[1], split[2], nil
}

func checkCalicoResourcesNotExist(args map[string]interface{}) error {
	// Loop through all the v3 resources to see if anything is returned
	for _, r := range allV3Resources {
		// Create mocked args in order to retrieve Get resources.
		mockArgs := map[string]interface{}{
			"<KIND>":   r,
			"<NAME>":   []string{},
			"--config": args["--config"].(string),
			"--export": false,
			"--output": "ps",
			"get":      true,
		}

		if _, ok := namespacedResources[r]; ok {
			mockArgs["--all-namespaces"] = true
		}

		// Get resources
		results := executeConfigCommand(mockArgs, actionGetOrList)

		// Loop through the result lists and see if anything exists
		for _, resource := range results.resources {
			if meta.LenList(resource) > 0 {
				return fmt.Errorf("Found existing Calico %s resource", results.singleKind)
			}

			if results.fileInvalid {
				return fmt.Errorf("Failed to execute command: %v", results.err)
			} else if results.err != nil {
				return fmt.Errorf("Failed to retrieve %s resources during datastore check: %v", resourceDisplayMap[r], results.err)
			}
		}
	}

	return nil
}

func updateClusterInfo(ctx context.Context, c client.Interface, clusterInfoJson []byte) error {
	// Unmarshal the etcd cluster info resource.
	migrated := apiv3.ClusterInformation{}
	err := json.Unmarshal(clusterInfoJson, &migrated)
	if err != nil {
		return fmt.Errorf("Error reading exported cluster info for migration: %s", err)
	}

	// Get the "default" cluster info resource.
	clusterinfo, err := c.ClusterInformation().Get(ctx, "default", options.GetOptions{})
	if err != nil {
		return fmt.Errorf("Error retrieving current cluster info for migration: %s", err)
	}

	// Update the calico version and cluster GUID.
	clusterinfo.Spec.ClusterGUID = migrated.Spec.ClusterGUID
	clusterinfo.Spec.CalicoVersion = migrated.Spec.CalicoVersion
	_, err = c.ClusterInformation().Update(ctx, clusterinfo, options.SetOptions{})
	if err != nil {
		return fmt.Errorf("Error updating current cluster info for migration: %s", err)
	}

	return nil
}

func updateV3Resources(data []byte) error {
	// Create tempfile so the v3 resources can be created using Apply
	tempfile, err := ioutil.TempFile("", "v3migration")
	if err != nil {
		return fmt.Errorf("Error while creating temporary v3 migration file: %s\n", err)
	}
	defer os.Remove(tempfile.Name())

	if _, err := tempfile.Write(data); err != nil {
		return fmt.Errorf("Error while writing to temporary v3 migration file: %s\n", err)
	}

	mockArgs := []string{"apply", "-f", tempfile.Name()}
	err = Apply(mockArgs)
	if err != nil {
		return fmt.Errorf("Failed to import v3 resources: %s\n", err)
	}

	return nil
}
