#!/bin/bash

set -x
set -e
date
pwd
git status

# We *must* remove all inner containers and images before removing the outer
# container. Otherwise the inner images will stick around and fill disk.
# https://github.com/jpetazzo/dind#important-warning-about-disk-usage
docker exec -t host1 bash -c 'docker rm -f $(docker ps -qa) ; \
                              docker rmi $(docker images -qa)' || true
docker rm -f host1 || true
docker run --privileged -v `pwd`:/code --name host1 -tid jpetazzo/dind

docker exec -t host1 bash -c \
 'while ! docker ps; do sleep 1; done && \
 cd /code && \
 ./build_node.sh && \
 ./create_binary.sh'

# Run the STs
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/mainline.sh'
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/add_container.sh'
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/add_ip.sh'
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/arg_parsing.sh'
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/profile_commands.sh'
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/no_powerstrip.sh'
docker exec -t host1 bash -c 'cd /code && sudo ./tests/st/diags.sh'

docker exec -t host1 bash -c 'docker rm -f $(docker ps -qa) ; \
                              docker rmi $(docker images -qa)' || true
docker rm -f host1 || true

echo "All tests have passed."
