
# User guide for 'calicoctl endpoint' commands

This sections describes the `calicoctl endpoint` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl endpoint' commands

Run

    calicoctl endpoint --help

to display the following help menu for the calicoctl endpoint commands.

```

Usage:
  calicoctl endpoint show [--host=<HOSTNAME>] [--orchestrator=<ORCHESTRATOR_ID>] [--workload=<WORKLOAD_ID>] [--endpoint=<ENDPOINT_ID>] [--detailed]
  calicoctl endpoint <ENDPOINT_ID> profile (append|remove|set) [--host=<HOSTNAME>] [--orchestrator=<ORCHESTRATOR_ID>] [--workload=<WORKLOAD_ID>]  [<PROFILES>...]
  calicoctl endpoint <ENDPOINT_ID> profile show [--host=<HOSTNAME>] [--orchestrator=<ORCHESTRATOR_ID>] [--workload=<WORKLOAD_ID>]

Description:
  Configure or show endpoints assigned to existing containers

Options:
 --detailed                         Show additional information
 --host=<HOSTNAME>                  Filters endpoints on a specific host
 --orchestrator=<ORCHESTRATOR_ID>   Filters endpoints created on a specific orchestrator
 --workload=<WORKLOAD_ID>           Filters endpoints on a specific workload
 --endpoint=<ENDPOINT_ID>           Filters endpoints with a specific endpoint ID

Examples:
    Show all endpoints belonging to 'host1':
        $ calicoctl endpoint show --host=host1

    Add a profile called 'profile-A' to the endpoint a1b2c3d4:
        $ calicoctl endpoint a1b2c3d4 profile append profile-A

    Add a profile called 'profile-A' to the endpoint a1b2c3d4, but faster,
    by providing more specific filters:
        $ calicoctl endpoint a1b2c3d4 profile append profile-A --host=host1 --orchestrator=docker --workload=f9e8d7e6

```

## calicoctl endpoint commands


### calicoctl endpoint show 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl endpoint show [--host=<HOSTNAME>] [--orchestrator=<ORCHESTRATOR_ID>] [--workload=<WORKLOAD_ID>] [--endpoint=<ENDPOINT_ID>] [--detailed]

    <WORKLOAD_ID>
    <HOSTNAME>
    <ENDPOINT_ID>
    <ORCHESTRATOR_ID>
```

Examples:

```
calicoctl endpoint show 
```

### calicoctl endpoint <ENDPOINT_ID> profile 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl endpoint <ENDPOINT_ID> profile (append|remove|set) [--host=<HOSTNAME>] [--orchestrator=<ORCHESTRATOR_ID>] [--workload=<WORKLOAD_ID>]  [<PROFILES>...]

    <ENDPOINT_ID>
    <HOSTNAME>
    <PROFILES>
    <ORCHESTRATOR_ID>
    <WORKLOAD_ID>
```

Examples:

```
calicoctl endpoint <ENDPOINT_ID> profile 
```

### calicoctl endpoint <ENDPOINT_ID> profile show 

***DELETE AS APPROPRIATE***
This command can be run on any Calico node.  This command must be run as root
and must be run on the specific Calico node that you are configuring.

Command syntax:

```
calicoctl endpoint <ENDPOINT_ID> profile show [--host=<HOSTNAME>] [--orchestrator=<ORCHESTRATOR_ID>] [--workload=<WORKLOAD_ID>]

    <ENDPOINT_ID>
    <HOSTNAME>
    <ORCHESTRATOR_ID>
    <WORKLOAD_ID>
```

Examples:

```
calicoctl endpoint <ENDPOINT_ID> profile show 
```
