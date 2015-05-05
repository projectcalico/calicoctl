# This Dockerfile builds the simulated hosts in which we will run another docker process

# Made for running docker in docker. For details and docs - see https://github.com/jpetazzo/dind
FROM jpetazzo/dind

RUN cd ./calico_node && \
    ./build_node.sh && \
    cd ../build_calicoctl && \
    ./create_binary.sh && \
    cd ..
