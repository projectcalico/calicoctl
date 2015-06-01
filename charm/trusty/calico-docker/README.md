# Calico Docker Charm

Calico has redefined the way to build out data center networks using a pure
Layer 3 approach that is simpler, higher scaling, better performing and more
efficient than the standard approach of using overlay networks.

Removing the packet encapsulation associated with the standard Layer 2 solution
simplifies diagnostics, reduces transport overhead and improves performance.

The Calico approach of using a pure IP network combined with BGP for route
distribution allows internet scaling for virtual networks.

# Deployment

You will need a few Juju Dependencies to get started, if you have not installed
them prior:

    add-apt-repository ppa:juju/stable
    apt-get install juju juju-deployer

clone the calico-docker repository:

    git clone https://github.com/Metaswitch/calico-docker.git


Deploy the charm:

    export JUJU_REPOSITORY=calico-docker/charm
    juju-deployer -c calico-docker/charm/bundle/bundles.yaml

Run the Getting Started Example:

    juju action do calico-docker/0 core-one
    juju action do calico-docker/1 core-two

Both actions will output a UUID of the results, which are fetchable after the
run has completed:

    juju action fetch <uuid>

## Preparing for Scale

Calico-Docker is a subordinate charm, and scales with the docker service to
provide SDN across each of the hosts. To scale your cluster and add more nodes
simply scale the `docker` service. For example, to add 3 additional nodes to
the cluster:

    juju add-unit docker -n 3


# Configurable Options

The calico-node image is configurable, to limit the possiblity of having
differing versions of the calico-node image, it's suggested to lock the version
in the charm configuration so each unit you add at scale will use the proper
image.

    juju set calico-docker docker-image=calico/node:v0.4.2

The calicoctl tool is also versioned, along with a sha256 sum to ensure the
payload is delivered correctly:

    juju set calico-docker calicoctl-package=https://github.com/Metaswitch/calico-docker/releases/download/v0.4.2/calicoctl
    juju set calico-docker calicoctl-sum=90cd21fed0abae9ed524c95d3cff8192dfc133150cdf386951ed9daa28c2d889

## Maintainers:

- Charles Butler &lt;[charles.butler@canonical.com](mailto:charles.butler@canonical.com)&gt;
- Cory Benfield &lt;[cory.benfield@metaswitch.com](mailto:cory.benfield@metaswitch.com)&gt;

## Project Calico

- Upstream website
  - [projectcalico.org](http://projectcalico.org)
- Upstream Contact
  - [project calico contacts](http://www.projectcalico.org/contact/)
- Upstream bug tracker
  - [Calico-Docker bugtracker](https://github.com/Metaswitch/calico-docker/issues)
- Upstream mailing list or contact information
  - [Calico Mailing List](http://lists.projectcalico.org/listinfo/calico-tech)
