
# User guide for 'calicoctl pool' commands

This sections describes the `calicoctl pool` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl pool' commands

Run

    calicoctl pool --help

to display the following help menu for the calicoctl pool commands.

```

Usage:
  calicoctl pool (add|remove) <CIDRS>... [--ipip] [--nat-outgoing]
  calicoctl pool range add <START_IP> <END_IP> [--ipip] [--nat-outgoing]
  calicoctl pool show [--ipv4 | --ipv6]

Description:
  Configure IP Pools

Options:
  --ipv4          Show IPv4 information only
  --ipv6          Show IPv6 information only
  --nat-outgoing  Apply NAT to outgoing traffic
  --ipip          Use IP-over-IP encapsulation across hosts
 
```

## calicoctl pool commands


### calicoctl pool 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl pool (add|remove) <CIDRS>... [--ipip] [--nat-outgoing]

    <CIDRS>
```

Examples:

```
calicoctl pool 
```

### calicoctl pool range add <START_IP> <END_IP> 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl pool range add <START_IP> <END_IP> [--ipip] [--nat-outgoing]

    <START_IP>
    <END_IP>
```

Examples:

```
calicoctl pool range add <START_IP> <END_IP> 
```

### calicoctl pool show 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl pool show [--ipv4 | --ipv6]

    
```

Examples:

```
calicoctl pool show 
```
