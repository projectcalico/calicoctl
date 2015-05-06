# This Dockerfile builds the simulated hosts in which we will run another docker process

# Made for running docker in docker. For details and docs - see https://github.com/jpetazzo/dind
FROM jpetazzo/dind

ADD ./calico_node /calico_node
ADD ./build_calicoctl /build_calicoctl

WORKDIR /calico_node
RUN ./build_node.sh
WORKDIR /build_calicoctl
RUN ./create_binary.sh
