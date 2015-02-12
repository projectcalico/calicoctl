# For details and docs - see https://github.com/phusion/baseimage-docker#getting_started
FROM phusion/baseimage:0.9.16

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# Install Calico APT repo.  Note, we delay the apt-get update until 
# below so that the update is done in the same FS layer as the 
# install, making it unlikely to be out of sync.
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

# Confd
RUN curl -L https://github.com/kelseyhightower/confd/releases/download/v0.7.1/confd-0.7.1-linux-amd64 -o confd && \
    chmod +x confd

# Plugin
RUN pip install python-etcd

# Copy in files that belong in the home directory.
COPY home_overlay/* ./
# And those that belong relative to root.  E.g. /etc/service/...
COPY root_overlay/* /


