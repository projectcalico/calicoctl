# Calico on Docker

Calico can provide networking in a Docker environment. Each container gets its
own IP, there is no encapsulation and it can support massive scale. For more
details see http://www.projectcalico.org/technical/.

Development is very active at the moment so please Star this project and check
back often.

We welcome questions/comment/feedback (and pull requests).

* Mailing List - http://lists.projectcalico.org/listinfo/calico

* IRC -
  [#calico](http://webchat.freenode.net?randomnick=1&channels=%23calico&uio=d4)

* For Calico-on-Docker specific issues, please
  [raise issues](https://github.com/Metaswitch/calico-docker/issues/new) on
  Github.

## Getting started

To get started follow the instructions at
[Getting Started](docs/GettingStarted.md). They set up two CoreOS servers using
Vagrant, and run Calico components in containers to provide networking between
other guest containers.

## Orchestrator integration

For a lower level integration see [Orchestrators](docs/Orchestrators.md).

## What it covers

+ The Calico components run in Docker containers.

+ Calico provides network connectivity with security policy enforcement for
  other Docker containers.

+ IP-networked Docker containers available via `docker run` or the standard
  Docker API.  We use the excellent
  [Powerstrip](https://github.com/clusterhq/powerstrip) project to make this
  seamless.

+ Alongside the core services, we provide a simple commandline tool `calicoctl`
  for managing Calico.


## How does it work?

Calico connects datacenter workloads (containers, VMs, or bare metal) via IP no
matter which compute host they are on.  Read about it on the
[Project Calico website](http://www.projectcalico.org).  Endpoints are network
interfaces associated with workloads.

The `calico-master` container needs to run in one place in your cluster.  It
keeps track of all workloads & endpoints and distributes information to
`calico-node` containers that run on each Docker host you'll use with Calico.

The `calico-master` service instantiates:

+ the ACL Manager component

+ the Orchestrator Plugin component, backed by an
  [etcd](https://github.com/coreos/etcd) datastore.

The `calico-node` service is a worker that configures the network endpoints for
containers, handles IP routing, and installs policy rules.  It comprises:

+ Felix, the Calico worker process

+ BIRD, the routing process

+ a [Powerstrip](https://github.com/clusterhq/powerstrip) adapter to set up
  networking when Docker containers are created.

We provide a command line tool, `calicoctl`, which makes it easy to configure
and start the Calico services listed above, and allows you to interact with the
Orchestrator Plugin to define and apply network & security policy to the
containers you create.

    Usage:
      calicoctl master --ip=<IP>
                       [--etcd=<ETCD_AUTHORITY>]
                       [--master-image=<DOCKER_IMAGE_NAME>]
      calicoctl node --ip=<IP>
                     [--etcd=<ETCD_AUTHORITY>]
                     [--node-image=<DOCKER_IMAGE_NAME>]
      calicoctl status [--etcd=<ETCD_AUTHORITY>]
      calicoctl reset [--etcd=<ETCD_AUTHORITY>]
      calicoctl version [--etcd=<ETCD_AUTHORITY>]
      calicoctl addgroup <GROUP>  [--etcd=<ETCD_AUTHORITY>]
      calicoctl addtogroup <CONTAINER_ID> <GROUP>
                           [--etcd=<ETCD_AUTHORITY>]
      calicoctl diags
      calicoctl status
      calicoctl reset
    Options:
     --ip=<IP>                The local management address to use.
     --etcd=<ETCD_AUTHORITY>  The location of the etcd service as
                              host:port [default: 127.0.0.1:4001]
     --master-image=<DOCKER_IMAGE_NAME>  Docker image to use for
                              Calico's master container
                              [default: calico/master:v0.0.6]
     --node-image=<DOCKER_IMAGE_NAME>    Docker image to use for
                              Calico's per-node container
                              [default: calico/node:v0.0.6]

### Can a guest container have multiple networked IP addresses?

Using calicoctl we currently only support one IP address per container, but
more than one is possible if you use the lower level APIs.
