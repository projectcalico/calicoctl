
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

This command is used to gather diagnostic information from a Calico node.
This is usually used when trying to diagnose an issue that may be related to
your Calico network.

Optional flags allow you to specify which directory the diagnostics are
created in, and to automatically upload the diagnostics to http://transfer.sh
for easy sharing of the data.  Note that the uploaded files will be deleted
after 14 days.

This command must be run as root and must be run on the specific Calico node 
that you are gathering diagnostics for.

Command syntax:

```
calicoctl diags [--log-dir=<LOG_DIR>] [--upload]

Options:
  --log-dir=<LOG_DIR>  The directory for logs [default: /var/log/calico]
  --upload             Flag, when set, will upload logs to http://transfer.sh
```

Examples:

```
$ calicoctl diags --upload
Dumping netstat output
Dumping routes
Dumping iptables
Missing command: ipset
Error response from daemon: no such id: calico-node
Copying Calico logs
Dumping datastore
Diags saved to /tmp/tmp5o5omm/diags-120815_094543.tar.gz
Uploading file. Available for 14 days from the URL printed when the upload
completes

https://transfer.sh/8yfwb/diags-120815-094543.tar.gz
Done

```
