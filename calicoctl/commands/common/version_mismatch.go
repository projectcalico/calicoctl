// Copyright (c) 2021 Tigera, Inc. All rights reserved.

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

package common

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"

	log "github.com/sirupsen/logrus"

	"github.com/projectcalico/calicoctl/v3/calicoctl/commands/clientmgr"
	cerrors "github.com/projectcalico/libcalico-go/lib/errors"
	"github.com/projectcalico/libcalico-go/lib/options"
)

var VERSION string

func CheckVersionMismatch(configArg, allowMismatchArg interface{}) {
	if allowMismatch, _ := allowMismatchArg.(bool); allowMismatch {
		log.Infof("Skip version mismatch checking due to '--allow-version-mismatch' argument")

		return
	}

	cf, _ := configArg.(string)

	client, err := clientmgr.NewClient(cf)
	if err != nil {
		// If we can't connect to the cluster, skip the check. Either we're running a command that
		// doesn't need API access, in which case the check doesn't need to be run, or we'll
		// fail on the actual command.
		log.Infof("Skip version mismatch checking due to not being able to connect to the cluster")

		return
	}

	ctx := context.Background()

	ci, err := client.ClusterInformation().Get(ctx, "default", options.GetOptions{})
	if err != nil {
		var notFound cerrors.ErrorResourceDoesNotExist
		if errors.As(err, &notFound) {
			// ClusterInformation does not exist, so skip version check.
			log.Infof("Skip version mismatch checking due to ClusterInformation not being present")

			return
		}
		fmt.Fprintf(os.Stderr, "Unable to get Cluster Information to verify version mismatch: %s\n Use --allow-version-mismatch to override.\n", err)
		os.Exit(1)
	}

	clusterv := ci.Spec.CalicoVersion
	if clusterv == "" {
		// CalicoVersion field not specified in the cluster, so skip check.
		log.Infof("Skip version mismatch checking due to CalicoVersion not being set")

		return
	}

	clusterv = strings.Split(clusterv, "-")[0]

	clientv := strings.Split(VERSION, "-")[0]

	if clusterv != clientv {
		fmt.Fprintf(os.Stderr, "Version mismatch.\nClient Version:   %s\nCluster Version:  %s\nUse --allow-version-mismatch to override.\n", VERSION, clusterv)
		os.Exit(1)
	}
}
