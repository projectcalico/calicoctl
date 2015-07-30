
# User guide for 'calicoctl profile' commands

This sections describes the `calicoctl profile` commands.

Read the [calicoctl user guide](../calicoctl.md) for a full list of calicoctl commands.

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

### calicoctl profile add <PROFILE> 

### calicoctl profile remove <PROFILE>  

### calicoctl profile <PROFILE> tag show 

### calicoctl profile <PROFILE> tag  

### calicoctl profile <PROFILE> rule add  

### calicoctl profile <PROFILE> rule remove  

### calicoctl profile <PROFILE> rule show 

### calicoctl profile <PROFILE> rule json 

### calicoctl profile <PROFILE> rule update 

