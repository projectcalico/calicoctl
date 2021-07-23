// Copyright (c) 2019 Tigera, Inc. All rights reserved.

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

package utils

import (
	"os"
	"os/exec"
	"strings"

	. "github.com/onsi/gomega"
	log "github.com/sirupsen/logrus"

	"github.com/projectcalico/calicoctl/v3/calicoctl/commands"
)

var calicoctl = "/go/src/github.com/projectcalico/calicoctl/bin/calicoctl-linux-amd64"
var version_helper = "/go/src/github.com/projectcalico/calicoctl/tests/fv/helper/bin/calico_version_helper"

func getEnv(kdd bool) []string {
	env := []string{"ETCD_ENDPOINTS=http://127.0.0.1:2379"}

	if kdd {
		val, ok := os.LookupEnv("KUBECONFIG")
		if ok {
			env = []string{"KUBECONFIG=" + val, "DATASTORE_TYPE=kubernetes"}
		} else {
			env = []string{"K8S_API_ENDPOINT=http://localhost:8080", "DATASTORE_TYPE=kubernetes"}
		}
	}

	return env
}

func Calicoctl(kdd bool, args ...string) string {
	out, err := CalicoctlMayFail(kdd, args...)
	Expect(err).NotTo(HaveOccurred())
	return out
}

func CalicoctlMayFail(kdd bool, args ...string) (string, error) {
	cmd := exec.Command(calicoctl, args...)
	cmd.Env = getEnv(kdd)
	out, err := cmd.CombinedOutput()

	log.Infof("Run: calicoctl %v", strings.Join(args, " "))
	log.Infof("Output:\n%v", string(out))
	log.Infof("Error: %v", err)

	return string(out), err
}

func SetCalicoVersion(kdd bool, args ...string) (string, error) {
	// Set CalicoVersion in ClusterInformation
	var helperArgs []string

	cfgVal, ctxVal := commands.GetConfigAndContext(args)

	if cfgVal != "" {
		helperArgs = append(helperArgs, "--config="+cfgVal)
	}

	if ctxVal != "" {
		helperArgs = append(helperArgs, "--context="+ctxVal)
	}

	helperCmd := exec.Command(version_helper, helperArgs...)
	helperCmd.Env = getEnv(kdd)
	helperOut, helperErr := helperCmd.CombinedOutput()

	log.Infof("Run: %s %s", version_helper, strings.Join(helperArgs, " "))
	log.Infof("Output:\n%v", string(helperOut))
	log.Infof("Error: %v", helperErr)

	return string(helperOut), helperErr
}
