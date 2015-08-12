
# User guide for 'calicoctl container' commands

This sections describes the `calicoctl container` commands.

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


### calicoctl container <CONTAINER> ip 
This command


Command options:

```
    <CONTAINER>
```

Examples:

```
calicoctl container <CONTAINER> ip 
```

### calicoctl container <CONTAINER> endpoint
This command


Command options:

```
    <CONTAINER>
```

Examples:

```
calicoctl container <CONTAINER> endpoint
```

### calicoctl container add <CONTAINER> <IP> 
This command


Command options:

```
    <CONTAINER>
    <IP>
```

Examples:

```
calicoctl container add <CONTAINER> <IP> 
```

### calicoctl container remove <CONTAINER>
This command


Command options:

```
    <CONTAINER>
```

Examples:

```
calicoctl container remove <CONTAINER>
```
