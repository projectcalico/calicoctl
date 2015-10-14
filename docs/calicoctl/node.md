
# User guide for 'calicoctl node' commands

This sections describes the `calicoctl node` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl node' commands

Run

    calicoctl node --help

to display the following help menu for the calicoctl node commands.

```

Usage:
  calicoctl node [--ip=<IP>] [--ip6=<IP6>] [--node-image=<DOCKER_IMAGE_NAME>] [--as=<AS_NUM>] [--log-dir=<LOG_DIR>] [--detach=<DETACH>] [--kubernetes]
  calicoctl node stop [--force]
  calicoctl node bgp peer add <PEER_IP> as <AS_NUM>
  calicoctl node bgp peer remove <PEER_IP>
  calicoctl node bgp peer show [--ipv4 | --ipv6]

Description:
  Configure the main calico/node container as well as default BGP information
  for this node.

Options:
  --force                   Stop the node process even if it has active endpoints.
  --node-image=<DOCKER_IMAGE_NAME>    Docker image to use for Calico's per-node
                                      container [default: calico/node:latest]
  --detach=<DETACH>         Set "true" to run Calico service as detached,
                            "false" to run in the foreground. [default: true]
  --log-dir=<LOG_DIR>       The directory for logs [default: /var/log/calico]
  --ip=<IP>                 The local management address to use.
  --ip6=<IP6>               The local IPv6 management address to use.
  --as=<AS_NUM>             The default AS number for this node.
  --ipv4                    Show IPv4 information only.
  --ipv6                    Show IPv6 information only.
  --kubernetes              Download and install the kubernetes plugin

```

## calicoctl node commands


### calicoctl node 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl node [--ip=<IP>] [--ip6=<IP6>] [--node-image=<DOCKER_IMAGE_NAME>] [--as=<AS_NUM>] [--log-dir=<LOG_DIR>] [--detach=<DETACH>] [--kubernetes]

    <DOCKER_IMAGE_NAME>
    <IP>
    <IP6>
    <DETACH>
    <AS_NUM>
    <LOG_DIR>
```

Examples:

```
calicoctl node 
```

### calicoctl node stop 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl node stop [--force]

    
```

Examples:

```
calicoctl node stop 
```

### calicoctl node bgp peer add <PEER_IP> as <AS_NUM>

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl node bgp peer add <PEER_IP> as <AS_NUM>

    <AS_NUM>
    <PEER_IP>
```

Examples:

```
calicoctl node bgp peer add <PEER_IP> as <AS_NUM>
```

### calicoctl node bgp peer remove <PEER_IP>

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl node bgp peer remove <PEER_IP>

    <PEER_IP>
```

Examples:

```
calicoctl node bgp peer remove <PEER_IP>
```

### calicoctl node bgp peer show 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl node bgp peer show [--ipv4 | --ipv6]

    
```

Examples:

```
calicoctl node bgp peer show 
```
