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

package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	log "github.com/sirupsen/logrus"
)

var supportedCmds = []string{"apply", "delete"}

func main() {

	// Check the number of Arguments passed
	if len(os.Args) < 3 {
		log.Fatal("Not enough Arguments passed, expected format calicoctl-util apply /tmp")
		return
	}

	err := processArgs()
	if err != nil {
		os.Exit(1)
	}
}

func processArgs() error {

	var args []string
	// cache all the arguments locally
	args = append(args, os.Args...)

	// check supported command is passed
	cmd := args[1]
	checkCmd := func() bool {
		for _, val := range supportedCmds {
			if val == cmd {
				return true
			}
		}
		return false
	}

	ok := checkCmd()
	if !ok {
		log.WithField("Command: ", cmd).Error("Unsupported Command passed as an argument")
		return fmt.Errorf("Unsupported command :%s passed in argument", cmd)
	}

	// check the path information
	path := args[2]
	info, err := os.Stat(path)
	if os.IsNotExist(err) {
		log.WithError(err).Error("Path does not exist")
		return err
	}

	// If the given path is directory, process all manifests
	if info.IsDir() {
		err = processManifests(cmd, path)
	}

	// If the given path is a file, process the manifest
	if info.Mode().IsRegular() {
		err = processManifest(cmd, path)
	}

	return err
}

// Process manifest file
func processManifest(cmd, path string) error {

	calicoCtlCmd := exec.Command("/calicoctl", cmd, "-f", path)
	stdOut, stdErr, err := runCommand(calicoCtlCmd)
	if err != nil {
		log.WithFields(log.Fields{
			"Error ": stdErr,
			"Cmd ":   cmd,
			"Path ":  path,
		}).WithError(err).Error("Failed to apply Manifests")
	} else {
		log.WithFields(log.Fields{
			"Output ": stdOut,
			"Cmd ":    cmd,
			"Path ":   path,
		}).Info("Manifest applied successfully")
	}
	return err
}

// Traverse all files in a directory, and process all manifests
func processManifests(cmd, dir string) error {

	err := filepath.Walk(dir,
		func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			if info.IsDir() {
				return nil
			}

			ext := strings.ToLower(filepath.Ext(path))
			if ext == ".yaml" || ext == ".yml" {
				err = processManifest(cmd, path)
			} else {
				log.Infof("Unsupported file :%s", path)
			}

			return err
		})

	return err
}

// Get std output and error by executing the command
func runCommand(cmd *exec.Cmd) (string, string, error) {

	var stderrBuffer, stdoutBuffer bytes.Buffer
	cmd.Stderr = &stderrBuffer
	cmd.Stdout = &stdoutBuffer
	err := cmd.Run()

	stdOut := stdoutBuffer.String()
	stdErr := stderrBuffer.String()
	return stdOut, stdErr, err
}
