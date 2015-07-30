
# User guide for 'calicoctl bgp' commands

This sections describes the `calicoctl bgp` commands.

Read the [calicoctl user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl bgp' commands

Run

    calicoctl bgp --help

to display the following help menu for the calicoctl bgp commands.

```

Usage:
  calicoctl bgp peer add <PEER_IP> as <AS_NUM>
  calicoctl bgp peer remove <PEER_IP>
  calicoctl bgp peer show [--ipv4 | --ipv6]
  calicoctl bgp node-mesh [on|off]
  calicoctl bgp default-node-as [<AS_NUM>]


Description:
  Configure default global BGP settings for all nodes. Note: per-node settings
  will override these globals for that node.

Options:
 --ipv4    Show IPv4 information only.
 --ipv6    Show IPv6 information only.

```

## calicoctl bgp commands

### calicoctl bgp peer add <PEER_IP> as <AS_NUM> 

### calicoctl bgp peer remove <PEER_IP> 

### calicoctl bgp peer show  

### calicoctl bgp node 

### calicoctl bgp default 

