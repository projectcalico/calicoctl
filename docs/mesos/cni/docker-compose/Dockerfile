FROM djosborne/mesos-modules-dev-phusion:master
MAINTAINER Dan Osborne <dan@projectcalico.org>

####################
# Mesos-DNS
####################
RUN curl -LO https://github.com/mesosphere/mesos-dns/releases/download/v0.5.0/mesos-dns-v0.5.0-linux-amd64 && \
    mv mesos-dns-v0.5.0-linux-amd64 /usr/bin/mesos-dns && \
    chmod +x /usr/bin/mesos-dns

###################
# Docker
###################
RUN apt-get update -qq && apt-get install -qqy \
    apt-transport-https \
    ca-certificates \
    curl \
    lxc \
    iptables

# Install Docker from Docker Inc. repositories.
RUN curl -sSL https://get.docker.com/ | sh

# Define additional metadata for our image.
VOLUME /var/lib/docker

#################
# Init scripts
#################
ADD ./init_scripts/etc/service/mesos_slave/run /etc/service/mesos_slave/run
ADD ./init_scripts/etc/service/docker/run /etc/service/docker/run
ADD ./init_scripts/etc/service/calico/run /etc/service/calico/run
ADD ./init_scripts/etc/service/mesos-dns/run /etc/service/mesos-dns/run
ADD ./init_scripts/etc/config/mesos-dns.json /etc/config/mesos-dns.json


######################
# Calico
######################
COPY ./calico/ /calico/
ADD https://github.com/projectcalico/calico-docker/releases/download/v0.19.0/calicoctl /usr/local/bin/calicoctl 
RUN chmod +x /usr/local/bin/calicoctl
ADD https://github.com/projectcalico/calico-cni/releases/download/v1.3.0/calico /cni/bin/calico
RUN chmod +x /cni/bin/calico
ADD https://github.com/projectcalico/calico-cni/releases/download/v1.3.0/calico-ipam /cni/bin/calico-ipam
RUN chmod +x /cni/bin/calico-ipam

ADD ./cni/ /cni/
