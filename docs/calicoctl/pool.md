
# User guide for 'calicoctl pool' commands

This sections describes the `calicoctl pool` commands.

Read the [calicoctl user guide](../calicoctl.md) for a full list of calicoctl commands.

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

### calicoctl pool range add <START_IP> <END_IP>  

### calicoctl pool show  

