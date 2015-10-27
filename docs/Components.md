# Calico Components
TODO: THIS DOC PROVIDES INFORMATION ABOUT THE COMPONENTS THAT MAKE UP A CALICO 
CLUSTER USING CONTAINERS.

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

## Anatomy of calico/node

`calico/node` can be regarded as a helper container that bundles together the 
various components required for Calico networking.  The image utilizes the 
following processes:

<!--
Diagram?: [Host [calico/node [Felix] [BIRD] [confd]] [etcd] [kernel [iptables] [FIB] [RIB]]]

- Felix has line to kernel for configuring kernel

- confd has dotted line to etcd for reading etcd, and line to BIRD for template config

- BIRD has dotted line to kernel for reading routes, and in/out line going outside
  of the host for BGP (sending/receiving routes to/from peers)

- etcd is DB shape
-->

#### Calico Felix agent
<!--
***TODO: Link to more detailed documentation.***
***TODO: Reword some of this, as per Rob's email.***
-->

The Felix daemon is the heart of Calico networking.  Felix's primary job is to 
program routes and ACL's on a workload host to provide desired connectivity to 
and from workloads on the host.  Felix programs 
endpoint routes of workloads into the host's Linux kernel FIB table so that packets 
to endpoints arrive on the host and then forward to the correct endpoint.

Felix also programs interface information to the kernel for outgoing endpoint 
traffic. Felix instructs the host to respond to ARPs for workloads with the 
MAC address of the host.

#### BIRD internet routing daemon

BIRD is an open source BGP client that is used to exchange routing information 
between hosts.  The routes that Felix programs into the kernel for endpoints 
are picked up by BIRD and distributed to BGP peers on the network, which 
provides inter-host routing.

#### confd templating engine 

The confd templating engine watches the etcd datastore for any changes to BGP 
configuration.  Confd dynamically generates BIRD configuration files based on 
these changes, then triggers BIRD to load the new files.  Confd also watches 
IPAM information to filter exported routes and handle route aggregation.

