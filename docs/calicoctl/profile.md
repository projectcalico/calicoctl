
# User guide for 'calicoctl profile' commands

This sections describes the `calicoctl profile` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

## Displaying the help text for 'calicoctl profile' commands

Run

    calicoctl profile --help

to display the following help menu for the calicoctl profile commands.

```

Usage:
  calicoctl profile show [--detailed]
  calicoctl profile add <PROFILE>
  calicoctl profile remove <PROFILE> [--no-check]
  calicoctl profile <PROFILE> tag show
  calicoctl profile <PROFILE> tag (add|remove) <TAG>
  calicoctl profile <PROFILE> rule add (inbound|outbound) [--at=<POSITION>]
    (allow|deny) [(
      (tcp|udp) [(from [(ports <SRCPORTS>)] [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
                [(to   [(ports <DSTPORTS>)] [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
      icmp [(type <ICMPTYPE> [(code <ICMPCODE>)])]
           [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
           [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
      [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
      [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])]
    )]
  calicoctl profile <PROFILE> rule remove (inbound|outbound) (--at=<POSITION>|
    (allow|deny) [(
      (tcp|udp) [(from [(ports <SRCPORTS>)] [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
                [(to   [(ports <DSTPORTS>)] [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
      icmp [(type <ICMPTYPE> [(code <ICMPCODE>)])]
           [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
           [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
      [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
      [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])]
    )])
  calicoctl profile <PROFILE> rule show
  calicoctl profile <PROFILE> rule json
  calicoctl profile <PROFILE> rule update

Description:
  Modify available profiles and configure rules or tags.

Options:
  --detailed        Show additional information.
  --no-check        Remove a profile without checking if there are endpoints
                    associated with the profile.
  --at=<POSITION>   Specify the position in the chain where the rule should
                    be placed. Default: append at end.

Examples:
  Add and set up a rule to prevent all inbound traffic except pings from the 192.168/16 subnet
  $ calicoctl profile add only-local-pings
  $ calicoctl profile only-local-pings rule add inbound deny icmp
  $ calicoctl profile only-local-pings rule add inbound --at=0 allow from 192.168.0.0/16

```

## calicoctl profile commands


### calicoctl profile show 
This command


Command syntax:

```
calicoctl profile show [--detailed]

    
```

Examples:

```
calicoctl profile show 
```

### calicoctl profile add <PROFILE>
This command


Command syntax:

```
calicoctl profile add <PROFILE>

    <PROFILE>
```

Examples:

```
calicoctl profile add <PROFILE>
```

### calicoctl profile remove <PROFILE> 
This command


Command syntax:

```
calicoctl profile remove <PROFILE> [--no-check]

    <PROFILE>
```

Examples:

```
calicoctl profile remove <PROFILE> 
```

### calicoctl profile <PROFILE> tag show
This command


Command syntax:

```
calicoctl profile <PROFILE> tag show

    <PROFILE>
```

Examples:

```
calicoctl profile <PROFILE> tag show
```

### calicoctl profile <PROFILE> tag 
This command


Command syntax:

```
calicoctl profile <PROFILE> tag (add|remove) <TAG>

    <PROFILE>
    <TAG>
```

Examples:

```
calicoctl profile <PROFILE> tag 
```

### calicoctl profile <PROFILE> rule add 
This command


Command syntax:

```
calicoctl profile <PROFILE> rule add (inbound|outbound) [--at=<POSITION>]
  (allow|deny) [(
    (tcp|udp) [(from [(ports <SRCPORTS>)] [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
              [(to   [(ports <DSTPORTS>)] [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
    icmp [(type <ICMPTYPE> [(code <ICMPCODE>)])]
         [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
         [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
    [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
    [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])]
  )]

    <SRCCIDR>
    <PROFILE>
    <DSTTAG>
    <DSTPORTS>
    <POSITION>
    <ICMPCODE>
    <DSTCIDR>
    <SRCTAG>
    <SRCPORTS>
    <ICMPTYPE>
```

Examples:

```
calicoctl profile <PROFILE> rule add 
```

### calicoctl profile <PROFILE> rule remove 
This command


Command syntax:

```
calicoctl profile <PROFILE> rule remove (inbound|outbound) (--at=<POSITION>|
  (allow|deny) [(
    (tcp|udp) [(from [(ports <SRCPORTS>)] [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
              [(to   [(ports <DSTPORTS>)] [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
    icmp [(type <ICMPTYPE> [(code <ICMPCODE>)])]
         [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
         [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])] |
    [(from [(tag <SRCTAG>)] [(cidr <SRCCIDR>)])]
    [(to   [(tag <DSTTAG>)] [(cidr <DSTCIDR>)])]
  )])

    <SRCCIDR>
    <PROFILE>
    <DSTTAG>
    <DSTPORTS>
    <POSITION>
    <ICMPCODE>
    <DSTCIDR>
    <SRCTAG>
    <SRCPORTS>
    <ICMPTYPE>
```

Examples:

```
calicoctl profile <PROFILE> rule remove 
```

### calicoctl profile <PROFILE> rule show
This command


Command syntax:

```
calicoctl profile <PROFILE> rule show

    <PROFILE>
```

Examples:

```
calicoctl profile <PROFILE> rule show
```

### calicoctl profile <PROFILE> rule json
This command


Command syntax:

```
calicoctl profile <PROFILE> rule json

    <PROFILE>
```

Examples:

```
calicoctl profile <PROFILE> rule json
```

### calicoctl profile <PROFILE> rule update
This command


Command syntax:

```
calicoctl profile <PROFILE> rule update

    <PROFILE>
```

Examples:

```
calicoctl profile <PROFILE> rule update
```
