# Getting Started with Calico

## Components of Basic Calico Container Deployments

All basic Calico deployments require the following components:

 - **`calico/node`**: Docker image that runs the underlying calico processes (see 
   ***Anatomy of calico/node*** below). The `calico/node` image must be deployed 
   on each host in the network.


 - **`calicoctl`**: The command line tool responsible for configuring all of the 
   networking components within Calico, including endpoint addresses, security 
   policies, and BGP peering.


 - **Orchestrator (Docker, Kubernetes, etc)**: Manages container creation/deletion 
   and runs the `calico/node` Docker image as a container. (See the [Calico 
   Orchestrators page](./Orchestrators.md) for details on integration)


 - [**etcd**](https://github.com/coreos/etcd): Datastore used by Calico to store 
   endpoint, bgp, and policy data that can be accessed by all of the hosts.

<!--
*** Short description of how example below has etcd running on 
 single host where the host is the ETCD_AUTHORITY. Other hosts access data by 
 connecting to the host over port 2379.***

***TODO: Link to more detailed reading about Calico networking?***
-->

## Networking options

With each of these tutorials we provide details for running the demonstration 
using manual setup on your own servers, or with a quick set-up in a virtualized
environment using Vagrant, or a number of cloud services.

Worked examples are available for demonstrating Calico networking with the 
following different networking options.

### Docker default networking

This uses Dockers standard networking infrastructure, requiring you to 
explicitly add a created container into a Calico network.

This is compatible with all Docker versions from 1.6 onwards.

### Docker with libnetwork

Docker's native [libnetwork network driver][libnetwork] is available in the 
Docker 1.9 release currently underoing development.

Setup of the libnetwork environment is a little more involved since it requires
the current master (1.9.dev) builds of Docker, and the use of etcd as a
datastore for Docker clustering.

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


## Demonstrations

Once your environment has been configured, you can run through the 
demonstrations below:
  - [Docker Default Networking](default-networking/Demonstration.md)
    - For IPv6, use the [Docker Default IPv6 guide](default-networking/DemonstrationIPv6.md)
  - [Docker libnetwork](libnetwork/Demonstration.md)
    - For IPv6, use the [libnetwork IPv6 guide](libnetwork/DemonstrationIPv6.md)

## Orchestrator Integrations

If you'd like to use Calico with an Orchestrator, checkout the Calico 
integration docs below.

  - [Kubernetes](kubernetes/README.me)
  - See the [Orchestrators page](../Orchestrators.md) for more information 
    about using Calico with Orchestrators.