# Integrating the Calico Network Plugin with rkt

This guide will describe the configuration required to use the Calico network plugin in your rkt deployment.

## Using rkt Plugins

This guide will assume you already have a working rkt deployment.

If not, the CoreOS [documentation](https://github.com/coreos/rkt/blob/master/Documentation/networking.md) for Network Plugins will walk you through the basics of setting up networking in rkt.

## Requirements

In order to run Calico in your rkt deployment, you will need:
* A working [etcd](https://github.com/coreos/etcd) service.
* A build of `calicoctl` after [v0.7.0](https://github.com/projectcalico/calico-docker/releases).
* A working [docker](https://github.com/docker/docker) service. (Although Calico is capable of networking rkt containers, our core software is distributed and deployed in a [docker container](https://github.com/projectcalico/calico-docker/blob/master/docs/getting-started/default-networking/Demonstration.md). While we work on native rkt support, you will need to run Calico in Docker before starting your rkt containers.)

## Installing

We recommend installing the plugin using the following `calicoctl` command. This will run our Docker agent, as well as install the plugin.

```calicoctl node --ip=<IP> --rkt```

Including the `--rkt` command downloads the rkt plugin and moves it to the correct location. You can manually install the plugin by downloading one of our releases in the [calico-cni](https://github.com/projectcalico/calico-cni/releases) repo

## Configuration

Configure your network with a `*.conf` file. 
* The default file location is `/etc/rkt/net.d/`. If you choose to put the net configuration file in a different location, be sure to specify the path with the environment variable `CNI_PATH`. 
* Each network should have their own configuration file and must be given a unique `"name"`.
* To call the Calico plugin, set the `"type"` to `"calico"`.
* The `"ipam"` section must include the key `"type": "calico-ipam"` and specify an IP Pool in `"subnet"`. An IP address will be allocated from the indicated `"subnet"` pool.
```
# 10-calico.conf

{
    "name": "example_net",
    "type": "calico",
    "ipam": {
        "type": "calico-ipam",
        "subnet": "10.1.0.0/16"
    }
}
```