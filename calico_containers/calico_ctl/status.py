"""
TODO

Usage:
  calicoctl status
"""
import re
from utils import docker_client


def status(arguments):
    calico_node_info = filter(lambda container: "/calico-node" in
                              container["Names"],
                              docker_client.containers())
    if len(calico_node_info) == 0:
        print "calico-node container not running"
    else:
        print "calico-node container is running. Status: %s" % \
              calico_node_info[0]["Status"]

        apt_cmd = docker_client.exec_create("calico-node", ["/bin/bash", "-c",
                                           "apt-cache policy calico-felix"])
        result = re.search(r"Installed: (.*?)\s", docker_client.exec_start(apt_cmd))
        if result is not None:
            print "Running felix version %s" % result.group(1)

        print "IPv4 Bird (BGP) status"
        bird_cmd = docker_client.exec_create("calico-node",
                                    ["/bin/bash", "-c",
                                     "echo show protocols | "
                                     "birdc -s /etc/service/bird/bird.ctl"])
        print docker_client.exec_start(bird_cmd)
        print "IPv6 Bird (BGP) status"
        bird6_cmd = docker_client.exec_create("calico-node",
                                    ["/bin/bash", "-c",
                                     "echo show protocols | "
                                     "birdc6 -s "
                                     "/etc/service/bird6/bird6.ctl"])
        print docker_client.exec_start(bird6_cmd)