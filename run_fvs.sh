#!/bin/bash

set -x
set -e
date
pwd
git status

if $HOST; then
    docker build -t host ./host

    # Run the FVs
    docker exec host1 sudo ./tests/fv/arg_parsing.sh
    docker exec host1 sudo ./tests/fv/mainline.sh
    docker exec host1 sudo ./tests/fv/add_container.sh
    docker exec host1 sudo ./tests/fv/unix_socket.sh
    docker exec host1 sudo ./tests/fv/add_ip.sh
else
    ./build_node.sh
    pushd ./build_calicoctl
    ./create_binary.sh
    popd

    # Run the FVs
    sudo ./tests/fv/arg_parsing.sh
    sudo ./tests/fv/mainline.sh
    sudo ./tests/fv/add_container.sh
    sudo ./tests/fv/unix_socket.sh
    sudo ./tests/fv/add_ip.sh
fi

echo "All tests have passed."
