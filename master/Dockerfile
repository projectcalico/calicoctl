# For details and docs - see https://github.com/phusion/baseimage-docker#getting_started
FROM phusion/baseimage:0.9.16

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# Install Calico APT repo.  Note, we delay the apt-get update until 
# below so that the update is done in the same FS layer as the 
# install, making it unlnikely to be out of sync.
RUN curl -L http://binaries.projectcalico.org/repo/key | apt-key add - && \
    echo "deb http://binaries.projectcalico.org/repo ./" >> /etc/apt/sources.list && \
    echo "Package: *" >> /etc/apt/preferences &&\
    echo "Pin: origin binaries.projectcalico.org" >> /etc/apt/preferences && \
    echo "Pin-Priority: 1001" >> /etc/apt/preferences

# Do all the APT operations in one RUN call to ensure they're 
# consistent and minimize cruft build up in our layers.
RUN apt-get update && \
    apt-get install -qy \
        calico-felix \
        calico-acl-manager \
        curl \
        ipset \
        iptables \
        libffi-dev \
        libssl-dev \
        python-dev \
        python-docopt \
        python-pip \
        python-pyasn1 \
        python-zmq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Start ACL manager.
RUN mkdir /etc/service/aclmanager
COPY aclmanager.sh /etc/service/aclmanager/run

# Confd
RUN curl -L https://github.com/kelseyhightower/confd/releases/download/v0.7.1/confd-0.7.1-linux-amd64 -o confd && \
    chmod +x confd && \
    mkdir /etc/service/confd
COPY confd.sh /etc/service/confd/run

# Plugin
RUN pip install python-etcd
COPY plugin.py plugin.py
RUN mkdir /etc/service/pluginnetwork && \
    mkdir /etc/service/pluginendpoint
COPY plugin_network.sh /etc/service/pluginnetwork/run
COPY plugin_endpoint.sh /etc/service/pluginendpoint/run

COPY rc.local /etc/rc.local
COPY conf.d conf.d
COPY templates templates
RUN mkdir -p /config/data && \
    mkdir -p /var/log/calico

