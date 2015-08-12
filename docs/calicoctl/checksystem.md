
# User guide for 'calicoctl checksystem' commands

This sections describes the `calicoctl checksystem` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl checksystem' commands

Run

    calicoctl checksystem --help

to display the following help menu for the calicoctl checksystem commands.

```

Usage:
  calicoctl checksystem [--fix]

Description:
  Check for incompatibilities between calico and the host system

Options:
  --fix  Allow calicoctl to attempt to correct any issues detected on the host

```

## calicoctl checksystem commands

### calicoctl checksystem 
This command allows you to verify that your host system is configured correctly
for calicoctl to manage a Calico network.  The command may also, optionally,
attempt to correct any issues it discovers.

This command must be run as root, and is run on each host that will be running
a Calico node.

Command syntax:

```
calicoctl checksystem [--fix]

    --fix:  Allow calicoctl to attempt to correct any issues detected on the
            host.
            
    If the --fix option is omitted, the command provides a status report of 
    your host system indicating any issues.
```

Examples:

```
$ sudo calicoctl checksystem
WARNING: Unable to detect the xt_set module. Load with `modprobe xt_set`
WARNING: Unable to detect the ipip module. Load with `modprobe ipip`

$ sudo calicoctl checksystem --fix

```
