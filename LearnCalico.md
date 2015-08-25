# Calico networking in a containerized environment

This GitHub repository is the entry point for running a Calico network in a
containerized environment.

The repository provides:

-  A calico/node docker image that is used to run the Calico Felix agent 
(responsible for IP routing and ACL programming) and a BGP agent (BIRD) used
for distributing routes between hosts.
-  A command line tool `calicoctl` used for starting a calico/node container,
managing Calico poicy, orchestration tools used for adding and removing 
containers in a Calico network, and for certain network and diagnostic 
administration.

A number of additional GitHub repositories provide library functionality and
orchestration tools that are utilized by calicoctl.  These are listed below:

#### libcalico

 - Contains code for assigning IP addresses to endpoints, interfacing with 
   Linux namespaces, and storing data in the etcd datastore?

#### calico-kubernetes

 - Code implementing the calico plugin for running calico with kubernetes 
   orchestrator.  This is used when the calico node is started with the 
   --kubernetes flag.

#### calico-libnetwork

 - Code implementing calico plugin support for the Docker libnetwork 
   networking plugin.  This is used when the calico node is started with the 
   --libnetwork flag

#### calico-mesos

 - Code implementing the mesos plugin for running calico with mesos orchestrator.
   
#### calico-rkt

 - Code implementing the rkt plugin for running calico with rkt orchestrator.

***TODO: Add links to the above items and consider additional important notes 
about each.***

## Brief overview and Minimum Requirements

What actually is this?

The calico-docker networking plugin allows users to configure desired 
connectivity and policy of endpoints withing a containerized environment. 

Calico utilizes the following required integration components when working 
with containers:

 - calico/node: Docker image that runs the underlying calico processes (see 
 *Anatomy of calico/node* below).

 - calicoctl: The command line tool responsible for configuring all of the 
 networking components within Calico, including endpoint addresses, security 
 policies, and BGP peering.
   
 - Orchestrator (Docker, kubernetes, etc): Manages container creationg and runs 
 the calico/node docker image.

 - etcd: Datastore used by calico to store endpoint, bgp, and policy data that 
 can be accessed by all of the hosts.
*** Link to etcd. Short description of how example below has etcd running on 
 single host where the host is the ETCD_AUTHORITY. Other hosts access data by 
 connecting to the host over port 2379.***

***TODO: Link to more detailed reading about Calico networking.***

Diagram: [Host machine box [Orchestrator [calico/node]] [calicoctl]] where calicoctl
         has line to calicoctl with "configures" text.

## Anatomy of calico/node

***TODO: A quick upfront description of calico/node.***

***Can be regarded as a helper container to bundle together the various components
required for Calico networking.***

Diagram: [Host [calico/node [Felix] [BIRD] [confd]] [etcd] [Kernal [iptables] [FIB] [RIB]]]
         
- Felix has line to Kernal for configuring Kernal

- confd has dotted line to etcd for reading etcd, and line to BIRD for template config

- BIRD has dotted line to Kernal for reading routes, and in/out line going outside
  of the host for BGP (sending/receiving routes to/from peers)

- etcd is DB shape


#### Calico Felix agent

***TODO: Heart of the Calico networking.  Brief description.  Link to more detailed
documentation.***
The Felix daemon's primary job is to program routes and ACL's on a workload host 
to provide desired connectivity to and from workloads on the host.  Felix programs 
endpoint routes of workloads into the host's Linux Kernal FIB table so that packets 
to endpoints arrive on the host and then forward to the correct endpoint.

Felix also programs interface information to the kernal for outgoing endpoint 
traffic. Felix instructs the host to respond to ARPs for workloads with the 
MAC address of the host.  

#### BIRD internet routing daemon
 
***TODO: A BGP engine used to distribute routing information between hosts (for example
 how to get to a particular container IP on a different host)***

 - Read routing state the felix programs into the kernel and distribute around 
   data center

#### confd templating engine 

***TODO: Watches etcd configuration and dynamically generates, and triggers BIRD to load,
BIRD configuration files.***
 - Watches etcd datastore for changes in bgp data and triggers configuration
   changes in BIRD

## Lifecycle of a Calico networked container

### Start the calico/node instance on your container hosts

*** calicoctl adds BGP peering configuration and starts the calico/node container
*** Default configuration establishes a full BGP mesh between all of the nodes.
 - This uses a default AS number, though the default AS number and per-node AS number 
   are configurable
 - BGP peer information (IP and AS) stored in etcd
*** On Host 1, confd spots new hosts 
 - ...have been added to etcd's bgp data

*** Generates new BIRD templates containing the full set of other hosts as BGP peers

*** kicks BIRD to reload configuration

*** Mention other BGP topologies (e.g. mesh of RRs, calicoctl allows you to configure
this, but we won't discuss further in this document).

- etcd starts up, and calicoctl injects IP data about host to the bgp 

At this point we have a Felix running on each host, a BGP daemon running connected in a full mesh.
There are no containers and Felix is "standing by".
 - Confd continues to scan etcd data to compare against its own records.

Diagram:
[BASIC]
Two host setup where each host contains:
- orchestrator
  - calico/node (Felix, BIRD, confd)
- Kernal
- calicoctl
- etcd DB on Host1
- dotted etcd on Host2 

- calicoctl --[Host IP]-> etcd/bgp
- confd  <- - [Reads] - -  etcd, --[configure BGP]--> BIRD
- BIRD has BGP connection with other BRID

- HOSTS have connectivity

### Create some containers on your host

***TODO: What happens here???***

- Container is created by the orchestrator and remains with the orchestrator.

Containers are not networked, no IP address assignment at the moment other than 
Docker networking.

- Nothing has changed for Calico: BGP daemon is still running, Felix is still
  "standing by".

- Anything else to be said here? Is anything saved off at this point in etcd? Don't think so.

- libnetwork is different here, calico networking and profile is applied.

Diagram: Same as above, but calicoctl not programming anything, confd doesn't 
send anything to BIRD, BIRD still has BGP (as always from now on)

- No connectivity

### Add the containers to your Calico managed network

Use calicoctl to add containers to network and to provide container with an IP from a configured IP pool.

*** configures a veth pair, moving one end into container and one end remaining in host namespace.
 
 - Add container to calico networking by running `calicoctl container add <container> <ip_addr>`, 
   where the ip_addr is an ip address within the configured IP pool.  By default, the default 
   IPv4 pool for calico is `192.168.0.0/16`.  (You can view pools by running `calicoctl pool show`.) 
   To add a new pool, run `calicoctl pool add <cidr>` or `calicoctl pool range add <start_ip> <end_ip>`

- ETCD stores pool as: /calico/v1/ipam/v4/pool/192.168.0.0-16, where assigned 
  IPs in the pool are stored as: /calico/v1/ipam/v4/assignment/192.168.0.0-16/192.168.1.1

*** adds an Endpoint entry into etcd (Where???) the calico Felix configuration that tells Felix about the IP address
and MAC of the endpoint (the container interface), and the name of the host-side of the veth pair -- so that Felix
knows how to route to this IP address.

 - Felix detects this IP in etcd, programs route into Linux FIB with all traffic 
   heading to the IP sent to the veth in the host namespace, which is paired with 
   an IF on the container.

 - endpoint at: /calico/v1/host/<hostname:calico>/workload/<orchestrator>/<workload_id>/endpoint/<endpoint_id>

- Felix also programs basic config into the Linux ip tables allowing  
  outbound traffic from the container, but dropping all incoming traffic to the 
  container.
  
- BIRD sees routes in routing table and shares with BGP peers

*** mention that this is the default docker networking example, when running with an orchestrator
such as powerstrip, libnetwork, kubernetes the containers may be automatically added to the Calico
network as part of the container creation.  In these cases, the orchestrator plugin modules provide
the same function as the calicoctl commands for explicitly adding the container to the Calico network.

At this point there is no connectivity between containers as no network policy has been configured.

Diagram: Same as above, but:
- Each calicoctl --[configures endpoint]--> etcd
- Felix --[configure iptables rules and route to local routing table]--> Kernal
- Each BIRD <- - [Read] - - Kernal
- BIRD <--[endpoint routes]--> BIRD
- Each BIRD --[Program routes from other BIRD]-->Kernal


### Create a profile

What is a profile, where is it configured, how is it configured

- A profile represents a security policy that can be applied to any number of 
 containers in the calico network.  A profile is required in order for nodes to 
 be able to communicate with one another.

- Create a profile by calling `calicoctl profile add <profile>`

- etcd creates a new data point for the profile with associated rules and tags

- stored at /calico/v1/policy/profile/<profile>

- rules
{
  "inbound_rules": [{<rule>}, ...],
  "outbound_rules": [{<rule>}, ...]
}
where a <rule> is of format:
{
  "protocol": "tcp|udp|icmp|icmpv6",
  "src_tag": "<tag_name>",
  "src_net": "<CIDR>",
  "src_ports": [1234, "2048:4000"],
  "dst_tag": "<tag_name>",
  "dst_net": "<CIDR>",
  "dst_ports": [1234, "2048:4000"],
  "icmp_type": <int>,
  "action": "deny|allow",
}
profiles can be configured with calicoctl to allow configuration of all 
policy components listed above

- tags
["A", "B", "C", ...]
tags apply to all endpoints associated with this profile, and tags can be used 
in the rules (as shown above).

At this point, still no connectivity...

- ...because the profile has not yet been associated with any endpoints

- Felix has not done anything, BIRD has not done anything, libcalico has just 
  added an entry into etcd for the profile with default rules to allow all between 
  workloads that use this profile (currently none).


Diagram: Basic, but:
- calicoctl --[add profile]--> etcd
- No container connectivity

### Update your containers to use the profile

Mention that Felix deals with Endpoints rather than containers, but for simple
containers with a single interface managed using calicoctl - we treat a container and
endpoint as the same thing.  For more complicated scenarios, calicoctl provides
commands for managing actual endpoints.

What happens when add the profile to all of your container endpoints?

- etcd adds profile id to list of profiles associated with the endpoint_id

*** What does Felix do:

- Felix configures the Linux ip tables for endpoints based on the policy 
  described in the profile.  By default, this will allow all outgoing traffic 
  and all incoming traffic between containers/endpoints on the profile, but 
  deny all other incoming traffic.
TODO: Is this done using the interface or IP of the container?  How is the
rule applied to each endpoint?

*** BIRD?
 
- Bird has already distributed the routes of each container to each other host 
  in the calico network so it does not have any more work to do.

*** Voila connectivity between your endpoints

Diagram: Basic, but:
- calicoctl --[set profile in endpoint]--> etcd
- Felix --[set iptables rules]-->Kernal

-CONNECTIVITY between containers!

### More complicated policy

***TODO: Per node BGP, specific allow/deny, multiple profiles, 
- libnetwork differences.