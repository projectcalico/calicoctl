# Calico Repositories
TODO: THIS DOC WILL BE USED TO EXPLAIN THE REPOSITORY STRUCTURE OF CALICO IN A 
CONTAINERIZED ENVIRONMENT.

A number of GitHub repositories provide library functionality and
orchestration tools that are utilized by Calico.  This repository provides:

- `calico/node`: the Docker image used to run the Calico Felix agent 
  (responsible for IP routing and ACL programming) and a BGP agent (BIRD) 
  for distributing routes between hosts.
- `calicoctl`: the command line tool used for starting a `calico/node` container,
  configuring Calico policy, adding and removing containers in a Calico network via 
  orchestration tools, and managing certain network and diagnostic administration.

Additional libraries used by `calicoctl` and orchestration plugin repositories 
are listed below.

## Calico Libraries
 - [calico](https://github.com/projectcalico/calico): Implements the Felix 
   process that interfaces with the Linux kernel to configure routes and ACLs 
   that control network policy connectivity.  Felix runs as a process within 
   the `calico/node` container.

 - [libcalico](https://github.com/projectcalico/libcalico): Contains code for 
   assigning IP addresses to endpoints, interfacing with Linux namespaces, and 
   storing data in the etcd datastore.  The libcalico library is used by 
   `calicoctl`.

## Calico Orchestrator Integration Plugins
TODO: There are several integrations available for Calico in a containerized 
environment....

 - [calico-kubernetes](https://github.com/projectcalico/calico-kubernetes): 
   Implements the Calico plugin for running Calico with the 
   [kubernetes](https://github.com/kubernetes/kubernetes) orchestrator. This is 
   used when the Calico node is started with the `--kubernetes` flag.


 - [calico-mesos](https://github.com/projectcalico/calico-mesos): Implements 
   the Calico plugin for running Calico with the [mesos](https://github.com/apache/mesos) 
   orchestrator.


 - [calico-rkt](https://github.com/projectcalico/calico-rkt): Implements the 
   Calico plugin for running Calico with the [rkt](https://github.com/coreos/rkt) 
   orchestrator. This is used when the Calico node is started with the `--rkt` 
   flag.


 - [libnetwork-plugin](https://github.com/projectcalico/libnetwork-plugin): 
   Implements Calico plugin support for the Docker libnetwork networking plugin. 
   This is used when the Calico node is started with the `--libnetwork` flag.

TODO: For more information on these orchestrators and how to integrate Calico with 
your orchestrator, visit the [Calico Orchestrators document page](./Orchestrators.md).