<!--- master only -->
> ![warning](../images/warning.png) This document applies to the HEAD of the calico-docker source tree.
>
> View the calico-docker documentation for the latest release [here](https://github.com/projectcalico/calico-docker/blob/v0.12.0/README.md).
<!--- else
> You are viewing the calico-docker documentation for release **release**.
<!--- end of master only -->

# Running the Kubernetes Vagrant provider with Calico networking
Calico can be used as a network plugin for Kubernetes, to provide connectivity for workloads in a Kubernetes cluster.

The Kubernetes Vagrant provider can be configured to provision a local cluster with Calico networking.

# Prerequisites 
You'll need to make sure you meet the prerequisites laid out in: https://github.com/kubernetes/kubernetes/blob/master/docs/getting-started-guides/vagrant.md#prerequisites

## Getting Started
First, you'll need to check out a copy of the Kubernetes git repo. Currently the Calico Vagrant plugin code is waiting to be merged into the Kubernetes repo, so for now you'll need to check out our fork of the Kubernetes repo (which is based on the v1.1.2 release).
```
git clone -b calico-vagrant-integration https://github.com/caseydavenport/kubernetes.git
cd kubernetes
```

Now set the environment variables to specify the Calico Vagrant provisioner, and run the cluster init script from the root of the kubernetes repo:
```
export KUBERNETES_PROVIDER=vagrant
export NETWORK_PROVIDER=calico
export NUM_NODES=2
cluster/kube-up.sh
```

This will create a 2-node, 1-master cluster, with Calico providing network connectivity for Pods. 
