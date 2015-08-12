
# User guide for 'calicoctl diags' commands

This sections describes the `calicoctl diags` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl diags' commands

Run

    calicoctl diags --help

to display the following help menu for the calicoctl diags commands.

```

Usage:
  calicoctl diags [--log-dir=<LOG_DIR>] [--upload]

Description:
  Save diagnostic information

Options:
  --log-dir=<LOG_DIR>  The directory for logs [default: /var/log/calico]
  --upload             Flag, when set, will upload logs to http://transfer.sh

```

## calicoctl diags commands


### calicoctl diags 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl diags [--log-dir=<LOG_DIR>] [--upload]

    <LOG_DIR>
```

Examples:

```
calicoctl diags 
```
