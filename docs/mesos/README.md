<!--- master only -->
> ![warning](../images/warning.png) This document applies to the HEAD of the calico-docker source tree.
>
> View the calico-docker documentation for the latest release [here](https://github.com/projectcalico/calico-docker/blob/v0.13.0/README.md).
<!--- else
> You are viewing the calico-docker documentation for release **release**.
<!--- end of master only -->

# Mesos with Calico Networking
**Calico provides IP-Per-Container networking for Mesos clusters.** The following collection of tutorials will walk through the steps necessary for installation and use.

Questions? Contact us on the #Mesos channel of [Calico's Slack](https://calicousers-slackin.herokuapp.com/).

### Mesos Version Compatability
Calico support is actively being developed. Use the following information to ensure you choose the right version:
- **Mesos 0.26:** Recomended. Full Calico Support for the future.
- **Mesos 0.25:** Deprecated. Calico works with Mesos 0.25, but we recommend against using it as there aren't any Frameworks (including Marathon) which support the Networkinfo specs from 0.25 (which were modified for 0.26)
- **Mesos 0.24:** Unsupported. Calico works as a proof of concept, but is no longer supported.

### Support for Adding Calico to an Existing Mesos Cluster
The following tutorials cover installing Netmodules on a fresh machine which does not yet have Mesos installed.
This is because Calico requires Netmodules, a Mesos Networking Module, which must be compiled with the source header files of the active Mesos installation in order to ensure compatability. If your source installation files exist on your Mesos Slave, then it is possible to follow steps 1-3 and step 6 of the [Manual Calico-Mesos installation Guide](ManualInstallCalicoMesos.md) to add Netmodules and Calico to your existing cluster.

###  Launching Tasks with Calico + Mesos
IP-Per-Container Networking with Calico is an opt-in feature for Mesos Frameworks that launch tasks with [Networkinfo](https://github.com/apache/mesos/blob/0.26.0-rc3/include/mesos/mesos.proto#L1383). This means that your favorite Mesos Frameworks will not work with Calico until they have opted to include Networkinfo when launching tasks. Currently, this is limited to Mesos tasks launched via Marathon, with support for more frameworks growing. 

Since the Mesos Docker Containerizer does not support Module hooks, external networking is incompatible with docker containers in 0.26. Modifications are being made to the Mesos Containerizer to launch docker containers in future versions of Mesos, which will work with Calico out of the box going forward.

## 1. Prepare Master and Agent Nodes
The [Mesos Host Preparation tutorial](PrepareHosts.md) will walk you through hostname and firewall configuration for compatability between Calico and Mesos.

## 2. Prepare Core Services
Zookeeper and etcd serve as the backend datastores for Mesos and Calico, respectively. The [Core Services Preparation tutorial](PrepareCoreServices.md) will walk you through setting up both services using Docker.

## 3. Install
Choose one of the following guides to install Mesos with Calico:

### a.) RPM
The [Calico-Mesos RPM Installation Guide](RpmInstallCalicoMesos.md) serves as the fastest way to get up and running, by installing Mesos, Netmodules, and Calico onto your system.

### b.) Manual
For an in-depth walkthrough of the full installation procedure performed by the RPMs, see the [Calico-Mesos Manual Install Guide](ManualInstallCalicoMesos.md).

### c.) Dockerized Demo
Not interested in provisioning your own system? Folow the dockerized [net-modules demo][net-modules] to see how it all works.

## 4. Launching Tasks
Calico is compatible with all frameworks which use the new NetworkInfo protobuf when launching tasks. Marathon has introduced limited support for this. For an early peek, use `mesosphere/marathon:v0.14.0-RC1`:
```
$ docker run \
-e MARATHON_MASTER=zk://<ZOOKEEPER-IP>:2181/mesos \
-e MARATHON_ZK=zk://<ZOOKEEPER-IP>:2181/marathon \
-p 8080:8080 \
mesosphere/marathon:v0.14.0-RC1
```
This version of Marathon supports two new fields in an application's JSON file:

- `ipAddress`: Specifiying this field grants the application an IP Address networked by Calico.
- `group`: Groups are roughly equivalent to Calico Profiles. The default implementation isolates applications so they can only communicate with other applications in the same group. Assign a task the static `public` group to allow it to communicate with any other application.
 
> See [Marathon's IP-Per-Task documentation][marathon-ip-per-task-doc] for more information.

The Marathon UI has does not yet include a field for specifiying NetworkInfo, so we'll use the command line to launch an app with Marathon's REST API. Below is a sample `app.json` file that is configured to receive an address from Calico:
```
{
    "id":"/calico-apps",
    "apps": [
        {
            "id": "hello-world-1",
            "cmd": "ifconfig && sleep 30",
            "cpus": 0.1,
            "mem": 64.0,
            "ipAddress": {
                "groups": ["my-group-1"]
            }
        }
    ]
}
```

Send the `app.json` to marathon to launch it:
```
$ curl -X PUT -H "Content-Type: application/json" http://localhost:8080/v2/groups/calico-apps  -d @app.json
```

[calico]: http://projectcalico.org
[mesos]: https://mesos.apache.org/
[net-modules]: https://github.com/mesosphere/net-modules
[docker]: https://www.docker.com/
[marathon-ip-per-task-doc]: https://github.com/mesosphere/marathon/blob/v0.14.0-RC1/docs/docs/ip-per-task.md
[![Analytics](https://ga-beacon.appspot.com/UA-52125893-3/calico-docker/docs/mesos/README.md?pixel)](https://github.com/igrigorik/ga-beacon)
