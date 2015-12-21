<!--- master only -->
> ![warning](../images/warning.png) This document applies to the HEAD of the calico-docker source tree.
>
> View the calico-docker documentation for the latest release [here](https://github.com/projectcalico/calico-docker/blob/v0.13.0/README.md).
<!--- else
> You are viewing the calico-docker documentation for release **release**.
<!--- end of master only -->

# Manually Install Calico and Mesos
This tutorial will walk you through installing Mesos, Netmodules, and Calico onto a Centos host to create a Mesos Slave compatible with Calico.

## 1. Download the Calico Mesos Plugin
The Calico-Mesos plugin is available for download from the [calico-mesos repository releases](https://github.com/projectcalico/calico-mesos/releases). In this example, we will install the binary to the `/calico` directory.
    
        $ wget https://github.com/projectcalico/calico-mesos/releases/download/v0.1.1/calico_mesos
        $ chmod +x calico_mesos
        $ sudo mkdir /calico
        $ sudo mv calico_mesos /calico/calico_mesos

## 2. Create the modules.json Configuration File
To enable Calico networking in Mesos, you must create a `modules.json` file. When provided to the Mesos Agent process, this file will connect Mesos with the Net-Modules libraries as well as the Calico networking plugin, thus allowing Calico to receive networking events from Mesos.

    $ cat > /calico/modules.json <<EOF
    {
      "libraries": [
        {
          "file": "/opt/net-modules/libmesos_network_isolator.so", 
          "modules": [
            {
              "name": "com_mesosphere_mesos_NetworkIsolator", 
              "parameters": [
                {
                  "key": "isolator_command", 
                  "value": "/calico/calico_mesos"
                },
                {
                  "key": "ipam_command", 
                  "value": "/calico/calico_mesos"
                }
              ]
            },
            {
              "name": "com_mesosphere_mesos_NetworkHook" 
            }
          ]
        }
      ]
    }
    EOF

## 3. Run Calico Node
The last Calico component required for Calico networking in Mesos is `calico-node`, a Docker image containing Calico's core routing processes.
 
`calico-node` can easily be launched via `calicoctl`, Calico's command line tool. When doing so, we must point `calicoctl` to our running instance of etcd, by setting the `ECTD_AUTHORITY` environment variable.

> Follow our [Core Services Preparation tutorial](PrepareCoreServices.md) if you do not already have an instance of etcd running.

    $ wget https://github.com/projectcalico/calico-docker/releases/download/v0.9.0/calicoctl
    $ chmod +x calicoctl
    $ sudo ETCD_AUTHORITY=<IP of host with etcd>:4001 ./calicoctl node

## 4. Install Mesos / Netmodules Dependencies
Netmodules and Mesos both make use of the `protobuf`, `boost`, and `glog` libraries. To function correctly, Mesos and Netmodules must be built with identical compilations of these libraries. A standard Mesos installation will include bundled versions, so we'll compile Mesos with unbundled versions to ensure that netmodules is using precisely the same library as Mesos. First, download the libraries:
```
$ sudo yum install -y protobuf-devel protobuf-python boost-devel glog-devel
```
> Alternative to using the epel-release packages, you can manually compile these libraries yourself.

>A note on Glog: At the time of this writing, the `glog-devel` rpm package does not satisfy Mesos' glog dependency. If you encounter this issue, try manually compiling and installing glog v0.3.3 yourself. 

Next, install the picojson headers:

    $ wget https://raw.githubusercontent.com/kazuho/picojson/v1.3.0/picojson.h -O /usr/local/include/picojson.h

## 5. Build and Install Mesos
Next we'll follow the standard Mesos installation instructions, but pass a few flags to configure to use our installed libraries instead of the mesos bundled ones:
```
# Download Mesos source
$ git clone git://git.apache.org/mesos.git -b 0.26.0
$ cd mesos

# Configure and build.
$ ./bootstrap
$ mkdir build
$ cd build
$ ../configure --with-protobuf=/usr --with-boost=/usr --with-glog=/usr
$ make
$ sudo make install
```

## 6. Build and Install Netmodules
```
# Download netmodules source
$ git clone https://github.com/mesosphere/net-modules.git -b integration/0.26
$ cd net-modules/isolator

# Configure and build
$ ./bootstrap
$ mkdir build
$ cd build
$ ../configure --with-mesos=/usr/local --with-protobuf=/usr
$ make
$ sudo make install
```

## 7. Launch Mesos-Slave 
```
$ sudo ETCD_AUTHORITY=<ETCD-IP:PORT> /usr/local/sbin/mesos-slave \
--master=<MASTER-IP:PORT> \
--modules=file:///calico/modules.json \
--isolation=com_mesosphere_mesos_NetworkIsolator \
--hooks=com_mesosphere_mesos_NetworkHook
```
We provide the `ETCD_AUTHORITY` environment to variable here to allow the  `calico_mesos` plugin to function properly when called by `mesos-slave`. Be sure to replace it with the address of your running etcd server.

## 8. Launch Tasks
With your cluster up and running, you can now [Launch Tasks with Calico Networking using Marathon](README.md#4-launching-tasks).

[![Analytics](https://ga-beacon.appspot.com/UA-52125893-3/calico-docker/docs/mesos/ManualInstallCalicoMesos.md?pixel)](https://github.com/igrigorik/ga-beacon)
