
# User guide for 'calicoctl container' commands

This sections describes the `calicoctl container` commands.

These commands can be used to manage Calico networking for Docker containers.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl container' commands

Run

    calicoctl container --help

to display the following help menu for the calicoctl container commands.

```

Usage:
  calicoctl container <CONTAINER> ip (add|remove) <IP> [--interface=<INTERFACE>]
  calicoctl container <CONTAINER> endpoint-id show
  calicoctl container add <CONTAINER> <IP> [--interface=<INTERFACE>]
  calicoctl container remove <CONTAINER>

Description:
  Add or remove containers to calico networking and manage their assigned IP addresses.

Options:
  --interface=<INTERFACE>  The name to give to the interface in the container
                           [default: eth1]

```

## calicoctl container commands

### calicoctl container <CONTAINER> ip add <IP> 

This command allows you to add an IP address to a container that is already
using Calico networking.

This command must be run on the specific Calico node that hosts the container.

Command syntax:

```
calicoctl container <CONTAINER> ip add <IP> [--interface=<INTERFACE>]

Parameters:
    <CONTAINER>: The name or ID of the container
    <IP>: The IPv4 or IPv6 address to add.
    --interface=<INTERFACE>  The name to give to the interface in the container
                             [default: eth1]
    
```

Examples:

```
$ calicoctl container test-container ip add 192.10.0.3 --interface=eth1 
```

### calicoctl container <CONTAINER> ip remove <IP> 

This command allows you t remove an IP address from a container that is
using Calico networking.

This command must be run as root and must be run on the specific Calico node 
that hosts the container.

Command syntax:

```
calicoctl container <CONTAINER> ip remove <IP> [--interface=<INTERFACE>]

    <INTERFACE>: The name to give to the interface in the container
                 [default: eth1]
    <CONTAINER>: The name or ID of the container
    <IP>: The IPv4 or IPv6 address to add.
```

Examples:

```
$ calicoctl container test-container ip remove 192.10.0.3 --interface=eth1 
```

### calicoctl container <CONTAINER> endpoint-id show

This command allows you to view the IDs of the endpoint associated with
a container.  The endpoint ID is used by the 
[`calicoctl endpoint`](endpoint.md) commands for manipulating and viewing
endpoint configuration.

This command must be run on the specific Calico node that hosts the container.

Command syntax:

```
calicoctl container <CONTAINER> endpoint-id show

    <CONTAINER>: The name or ID of the container
```

Examples:

```
$ calicoctl container test-container endpoint-id show
```

### calicoctl container add <CONTAINER> <IP> 

This command allows you to add a container into the Calico network.

If you previously created your container using default Docker networking, then
use this command to set up Calico networking for this container.

This command must be run as root and must be run on the specific Calico node 
that hosts the container.

Command syntax:

```
calicoctl container add <CONTAINER> <IP> [--interface=<INTERFACE>]

    <INTERFACE>: The name to give to the interface in the container
                 [default: eth1]
    <CONTAINER>: The name or ID of the container
    <IP>: The IPv4 or IPv6 address to add.
```

Examples:

```
$ calicoctl container add test-container 192.10.0.3 --interface=eth1 
```

### calicoctl container remove <CONTAINER>

This command allows you to remove a container from the Calico network.

This command must be run as root and must be run on the specific Calico node 
that hosts the container.

Command syntax:

```
calicoctl container remove <CONTAINER>

    <CONTAINER>: The name or ID of the container
```

Examples:

```
$ calicoctl container remove test-container 
```
