> You are viewing the calico-containers documentation for release v0.17.0.

# Kubernetes with Calico networking
Calico can be used as a network plugin for Kubernetes using the Container Network Interface to provide connectivity for workloads in a Kubernetes cluster.  Calico is particularly suitable for large Kubernetes deployments on bare metal or private clouds, where the performance and complexity costs of overlay networks can become significant. It can also be used in public clouds.

To start using Calico Networking in your existing Kubernetes cluster, check out our [integration tutorial](KubernetesIntegration.md).

To build a new Kubernetes cluster with Calico networking, try one of the following guides:

Quick-start guides:
- [CoreOS Vagrant](VagrantCoreOS.md)
- [CoreOS on GCE](GCE.md)
- [CoreOS on AWS](AWS.md)

Bare-metal guides:
- [CoreOS bare-metal](https://github.com/caseydavenport/kubernetes/blob/calico-cni-coreos-doc/docs/getting-started-guides/coreos/bare_metal_calico.md)
- [Ubuntu bare-metal](https://github.com/caseydavenport/kubernetes/blob/calico-cni-ubuntu-doc/docs/getting-started-guides/ubuntu-calico.md)


# Kubernetes with Calico policy
Calico can provide network policy for Kubernetes clusters.  This feature is currently experimental and disabled by default. [The policy documentation](Policy.md) explains how to enable and use Calico policy in a Kubernetes cluster.

# Requirements
- The kube-proxy must be started in `iptables` proxy mode.

# Troubleshooting 
- [Troubleshooting](Troubleshooting.md)

[![Analytics](https://ga-beacon.appspot.com/UA-52125893-3/calico-containers/docs/cni/kubernetes/README.md?pixel)](https://github.com/igrigorik/ga-beacon)
