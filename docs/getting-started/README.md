<!--- master only -->
> ![warning](../images/warning.png) This document applies to the HEAD of the calico-docker source tree.
>
> View the calico-docker documentation for the latest release [here](https://github.com/projectcalico/calico-docker/blob/v0.9.0/README.md).
<!--- else
> You are viewing the calico-docker documentation for release **release**.
<!--- end of master only -->

# Getting Started with Calico

## Networking options

Worked examples are available for demonstrating Calico networking with the 
following different networking options.

### Docker default networking

This uses Dockers standard networking infrastructure, requiring you to 
explicitly add a created container into a Calico network.

This is compatible with all Docker versions from 1.6 onwards.

### Docker with libnetwork

Docker's native [libnetwork network driver][libnetwork] is available in the 
Docker 1.9 release.

## Environment Setup

There are several ways to set up your own Calico cluster.

Our automated setup guides are the fastest and easiest to get started using 
Calico.  They automatically install all of the required Calico components for 
you:

  - The **Calico Vagrant Installs** use vagrant with VirtualBox to automatically 
    install two Calico nodes on your local machine.
    - [CoreOS](./VagrantCoreOS.md)
    - [Ubuntu](./VagrantUbuntu.md)

  - The **Calico with Cloud Services** guides walk you through configuring your 
    desired cloud service with two hosts to run Calico networking.
    - [AWS](./AWS.md)
    - [GCE](./GCE.md)
    - [DigitalOcean](./DigitalOcean.md)

Alternatively you can configure your Calico components manually using the 
Environment Setup guides for [libnetwork](libnetwork/EnvironmentSetup.md) and 
[Docker default networking](default-networking/EnvironmentSetup.md).

Check out the [Calico Components page](../Components.md) for details on the 
basic requirements for a Calico deployment and information about the 
`calico/node` container networking backbone.

## Guides

Once your environment has been configured, you can run through the 
guides below:
  - [Docker Default Networking](default-networking/Demonstration.md)
    - For IPv6, use the [Docker Default IPv6 guide](default-networking/DemonstrationIPv6.md)
  - [Docker libnetwork](libnetwork/Demonstration.md)

## Orchestrator Integrations

This repository contains documentation for running [Calico with Kubernetes](../kubernetes/README.md) as well as [Calico with Mesos](../mesos/README.md)

If you'd like to use Calico with another orchestrator, check out the [Calico 
Repository Structure](../RepoStructure.md) page to see the available plugins.


[libnetwork]: https://github.com/docker/libnetwork