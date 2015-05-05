# This Dockerfile builds the simulated hosts in which we will run another docker process

# Made for running docker in docker. For details and docs - see https://github.com/jpetazzo/dind
FROM jpetazzo/dind

RUN pushd ./calico_node && \
    ./build_node.sh && \
    popd && \
    pushd ./build_calicoctl && \
    ./create_binary.sh && \
    popd
