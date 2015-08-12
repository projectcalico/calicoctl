
# User guide for 'calicoctl bgp' commands

This sections describes the `calicoctl bgp` commands.

These commands can be used to manage the global BGP configuration.  This 
includes default values to use for the AS number, whether a full BGP mesh is
required between all of the Calico nodes, and global BGP peers (these are BGP
speakers that peer with every Calico node in the network).

In addition to global BGP configuration, there is also Calico node specific
BGp configuration.  This provides mechanisms to set up BGP peers for an
individual Calico node, rather than all of the Calico nodes.  The node specific
BGP command options are discussed in the [calicoctl node](node.md) guide.

Read the [BGP guide](../bgp.md) for an overview of BGP configuration which
covers all available BGP related commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

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
This command is used to add a global BGP peer.

Command syntax:

```
  calicoctl bgp peer add <PEER_IP> as <AS_NUM>

    <PEER_IP>:  The IP address (IPv4 or IPv6) of the BGP peer
    <AS_NUM>:  The AS number of the BGP peer.
```

The peer is uniquely identified by the IP address, so if you add another peer
with the same IP address and different AS number, it will replace the previous
peer configuration.

Configuring a global peer instructs all Calico nodes in the deployment to 
establish a peering using the specified peer IP address and AS number.  If the 
AS number is the same as the AS number configured on the node, this will be an
iBGP connection, otherwise it will be an eBGP connection.

Examples:

```
$ calicoctl bgp peer add 192.0.2.10 as 64555

$ calicoctl bgp peer add 2001:0db8::1 as 64590
```

### calicoctl bgp peer remove <PEER_IP>
This command removes a global BGP peer that was previously added using 
`bgp peer add <PEER IP> as <AS_NUM>`.

The peer is uniquely identified by the IP address it was added with.

Removing a global peer instructs all Calico nodes in the deployment to delete 
the peering associated with the specified peer IP address.

Command syntax:

```
calicoctl bgp peer remove <PEER_IP>

    <PEER_IP>:  The IP address (IPv4 or IPv6) of the BGP peer
```

Examples:

```
$ calicoctl bgp peer remove 192.0.2.10
BGP peer removed from global configuration

$ calicoctl bgp peer remove 2001:0db8::1
BGP peer removed from global configuration
```

### calicoctl bgp peer show 
This command displays the current list of configured global BGP peers.

This command does not display the connection or protocol status of the peers.
If you want to view that information, use the [`calicoctl status`](status.md)
command.

Command syntax:

```
calicoctl bgp peer show [--ipv4 | --ipv6]

    --ipv4:  Optional flag to show IPv4 peers only
    --ipv6:  Optional flag to show IPv6 peers only
    
    If neither --ipv4 nor --ipv6 are specified, all peers are displayed.    
```

Examples:

```
$ calicoctl bgp peer show
+----------------------+--------+
| Global IPv4 BGP Peer | AS Num |
+----------------------+--------+
| 192.0.2.10           | 64555  |
+----------------------+--------+
+----------------------+--------+
| Global IPv6 BGP Peer | AS Num |
+----------------------+--------+
| 2001:db8::1          | 64590  |
+----------------------+--------+
 
$ calicoctl bgp peer show --ipv4
+----------------------+--------+
| Global IPv4 BGP Peer | AS Num |
+----------------------+--------+
| 192.0.2.10           | 64555  |
+----------------------+--------+ 
```

### calicoctl bgp node-mesh 
This command is used view the status of, or enable and disable, the full 
node-to-node BGP mesh.

When set to true, the Calico nodes automatically create a peering with all
other Calico nodes in the deployment.

Command syntax:

```
calicoctl bgp node-mesh [on|off]

    off:  Disable the node-to-node BGP mesh between all of the Calico nodes.
    on:  Enable the node-to-node BGP mesh between all of the Calico nodes.
    
    If no parameter is specified, this command displays the current status.
```

Examples:

```
$ calicoctl bgp node-mesh on

$ calicoctl bgp node-mesh off

$ calicoctl bgp node-mesh
off
```

### calicoctl bgp default
This command is used to view and set the default AS number used by Calico 
nodes.

When a Calico node is started (see [calicoctl node](node.md) commands)
the default AS number is used when confiburing the BGP peerings if one has not 
been explicitly specified for the node.

If any nodes are using the default AS number (i.e. it is not explicitly 
specified), then changing the default value with the following command will
automatically trigger the nodes to peer using the updated AS number.

Command syntax:

```
calicoctl bgp default-node-as [<AS_NUM>]

    <AS_NUM>: AS number to set as the default for all Calico nodes.
    
    If no parameter is specified, this command displays the current value.
```

Examples:

```
$ calicoctl bgp default-node-as 64512

$ calicoctl bgp default-node-as
64512
```
