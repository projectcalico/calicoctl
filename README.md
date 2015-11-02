<!--- master only -->
[![Build Status](https://semaphoreci.com/api/v1/projects/9d7d365d-19cb-4699-8c84-b76da25ae271/473490/shields_badge.svg)](https://semaphoreci.com/calico/calico-docker--5)
[![CircleCI branch](https://img.shields.io/circleci/project/projectcalico/calico-docker/master.svg?label=calicoctl)](https://circleci.com/gh/projectcalico/calico-docker/tree/master)
[![Coverage Status](https://coveralls.io/repos/projectcalico/calico-docker/badge.svg?branch=master&service=github)](https://coveralls.io/github/projectcalico/calico-docker?branch=master)
[![Docker Pulls](https://img.shields.io/docker/pulls/calico/node.svg)](https://hub.docker.com/r/calico/node/)
[![](https://badge.imagelayers.io/calico/node:latest.svg)](https://imagelayers.io/?images=calico/node:latest)

[![Slack Status](https://calicousers-slackin.herokuapp.com/badge.svg)](https://calicousers-slackin.herokuapp.com)
[![IRC Channel](https://img.shields.io/badge/irc-%23calico-blue.svg)](https://kiwiirc.com/client/irc.freenode.net/#calico)
<!--- end of master only -->

# Calico on Containers
As well as providing networking for OpenStack VMs, Calico can provide 
networking for containerized environments. Each container gets its 
own IP and fine grain security policy. In addition, Calico can be deployed 
without encapsulation or overlays to provide high performance at massive 
scales.  For more information on Project Calico see 
http://www.projectcalico.org/learn/.

Development is very active at the moment so please Star this project and check 
back often.

We welcome questions/comments/feedback (and pull requests).

* [Announcement Mailing List](http://lists.projectcalico.org/mailman/listinfo/calico-announce_lists.projectcalico.org)
* [Technical Mailing List](http://lists.projectcalico.org/mailman/listinfo/calico-tech_lists.projectcalico.org)
* [Slack Calico Users Channel](https://calicousers.slack.com) ([Sign up](https://calicousers-slackin.herokuapp.com))
* IRC - [#calico](https://kiwiirc.com/client/irc.freenode.net/#calico)
* For Calico-on-Docker specific issues, please [raise issues][raise-issues] on 
GitHub.

## How does it work?

Calico provides a highly scalable networking solution for connecting data 
center workloads (containers, VMs, or bare metal).  It is based on the same 
scalable IP networking principles as the internet, providing connectivity using
standard IP routing and isolation between workloads (or other fine grained
policy) using iptables programmed at the source and destination workloads.

Read more about it on the [Project Calico website][project-calico].

Project Calico uses [etcd][etcd] to distribute information about workloads, 
endpoints (a specific networking interface associated with a workload),
and policy to each Docker host.

The `calico-node` service is a worker that configures the network endpoints 
for containers, handles IP routing, and installs policy rules.  It runs in its 
own Docker container, and comprises
- Felix, the Calico worker process
- BIRD, the route distribution process

We provide a command line tool, `calicoctl`, which makes it easy to configure 
and start the Calico services listed above, and allows you to interact with 
the etcd datastore to define and apply network and security policy to the 
containers you create. Using `calicoctl`, you can provision Calico nodes, 
endpoints, and define and manage a rich set of security policy. 

## Getting Started

To get started using Calico, we recommend running through one or more of the 
available demonstrations from our [Getting Started](getting-started/README.md) 
guides.

These guides will help you understand the different networking options when 
using Calico by allowing you to configure and run a Calico cluster both locally 
and with your preferred cloud service.

With each of these tutorials we provide details for running the demonstration 
using manual setup on your own servers, a quick set-up in a virtualized
environment using Vagrant, or a number of cloud services.

We recommend using one of our quick set-up guides to start, such as the [Vagrant Ubuntu](docs/VagrantUbuntu.md) 
or [Vagrant CoreOS](docs/VagrantCoreos.md) guides for local installs or the 
[GCE](docs/GCE.md), [AWS](docs/AWS.md) or [DigitalOcean](docs/DigitcalOcean.md) 
guides for Calico with cloud services.

Also check out the [Calico Kubernetes integration](kubernetes/README.me) to 
learn how to configure Calico with the Kubernetes Orchestrator.

## Documenation
The Calico documentation provides information for both Calico users and 
developers.

  - **Learn how to configure Calico features in a deployment**
    - [BGP Configuration](docs/bgp.md) for managing global, node-to-node, and 
      node-specific BGP peers
    - [Logging Configuration](docs/logging.md) to set logging levels and choose 
      where Calico logs should be stored
    - [Advanced Network Policy](docs/AdvancedNetworkPolicy.md) to configure 
      security policy between Calico nodes and other networks
    - [External Connectivity](docs/ExternalConnectivity) for hosts on their own 
      Layer 2 segment
    - [`calicoctl` Reference Guide](docs/calicoctl.md) explains how the 
      `calicoctl` command line tool can be used to manage your Calico cluster
  - **Learn how Calico works under the covers**
    - [Calico Repository Structure](docs/RepoStructure.md) to see the tools 
      and repositories behind Calico and its integration plugin
    - [Calico Components](docs/Components.md) to see the required components 
      for a Calico integration 
    - [etcd Data Model Structure](docs/etcdStructure) for viewing how Calico 
      stores data for network and endpoint configurations
    - [Lifecycle of a Calico-Networked Docker Container](docs/DockerContainerLifecycle.md) 
      shows you what happens in Calico when containers are added to Calico 
      networking using Docker default networking
  - **Learn how to get involved with Calico builds and lower level integrations**
    - [Building Calico](docs/Building.md) to build a Calico setup on your local 
      machine for development and testing 
    - [Orchestrator Integration](docs/Orchestrators.md) for a lower level look 
      at Calico can be configured with an orchestrator
  - **FAQ and Troubleshooting**
    - [FAQ](docs/FAQ.md)
    - [Troubleshooting](docs/Troubleshooting.md)

[libnetwork]: https://github.com/docker/libnetwork
[raise-issues]: https://github.com/projectcalico/calico-docker/issues/new
[project-calico]: http://www.projectcalico.org
[etcd]: https://github.com/coreos/etcd
