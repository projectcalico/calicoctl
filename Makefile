.PHONY: all binary test ut vendor node_image force test-containerized

BUILD_CONTAINER_NAME=calico/calicoctl_build_container
BUILD_CONTAINER_MARKER=calicoctl_build_container.created

NODE_CONTAINER_DIR=calico_node
NODE_CONTAINER_FILES=$(shell find calico_node/ -type f ! -name '*.created')

# These variables can be overridden by setting an environment variable.
LOCAL_IP_ENV?=$(shell ip route get 8.8.8.8 | head -1 | cut -d' ' -f8)
HOST_CHECKOUT_DIR?=$(shell pwd)

default: binary node_image
all: test
test: ut

vendor:
	glide up

binary: dist/calicoctl

ut: binary
	./run-uts

st: run-etcd dist/calicoctl busybox.tgz routereflector.tgz calico-node.tgz calico-node-libnetwork.tgz
	# Use the host, PID and network namespaces from the host.
	# Privileged is needed since 'calico node' write to /proc (to enable ip_forwarding)
	# Map the docker socket in so docker can be used from inside the container
	# HOST_CHECKOUT_DIR is used for volume mounts on containers started by this one.
	# All of code under test is mounted into the container.
	#   - This also provides access to calicoctl and the docker client
	docker run --uts=host \
	           --pid=host \
	           --net=host \
	           --privileged \
	           -e HOST_CHECKOUT_DIR=$(HOST_CHECKOUT_DIR) \
	           -e DEBUG_FAILURES=$(DEBUG_FAILURES) \
	           --rm -ti \
	           -v /var/run/docker.sock:/var/run/docker.sock \
	           -v `pwd`:/code \
	           calico/test \
	           sh -c 'cp -ra tests/st/* /tests/st && cd / && nosetests $(ST_TO_RUN) -sv --nologcapture --with-timer $(ST_OPTIONS)'

calico-node.tgz:
	docker save calico/node:latest | gzip -c > calico-node.tgz

busybox.tgz:
	docker pull busybox:latest
	docker save busybox:latest | gzip -c > busybox.tgz

calico-node-libnetwork.tgz:
	docker pull calico/node-libnetwork:latest
	docker save calico/node-libnetwork:latest | gzip -c > calico-node-libnetwork.tgz

routereflector.tgz:
	docker pull calico/routereflector:latest
	docker calico/routereflector:latest | gzip -c > routereflector.tgz

semaphore: st

force:
	true

dist/calicoctl: force
	#mkdir -p dist
	#go build -o dist/calicoctl "./calicoctl/calicoctl.go"
	cp ../libcalico-go/bin/calicoctl dist/calicoctl.go

release/calicoctl: force
	mkdir -p release
	docker run \
		-v `pwd`/:/go/src/github.com/projectcalico/calico-containers/:ro \
		-v `pwd`/release/:/release/ \
		golang:1.7 sh -c \
		'cd /go/src/github.com/projectcalico/calico-containers && \
		go get -v ./calicoctl && \
		CGO_ENABLED=0 go build -o /release/calicoctl ./calicoctl'

# Build calicoctl in a container.
build-containerized: $(BUILD_CONTAINER_MARKER)
	docker run -ti --rm --privileged --net=host \
	-e PLUGIN=calico \
	-v ${PWD}:/go/src/github.com/tigera/libcalico-go:rw \
	$(BUILD_CONTAINER_NAME) make dist/calicoctl

# Run the tests in a container. Useful for CI, Mac dev.
test-containerized: $(BUILD_CONTAINER_MARKER)
	docker run -ti --rm --privileged --net=host \
	-e PLUGIN=calico \
	-v ${PWD}:/go/src/github.com/tigera/libcalico-go:rw \
	$(BUILD_CONTAINER_NAME) make ut

$(BUILD_CONTAINER_MARKER): Dockerfile.build
	docker build -f Dockerfile.build -t $(BUILD_CONTAINER_NAME) .
	touch $@

# Etcd is used by the tests
run-etcd:
	@-docker rm -f calico-etcd
	docker run --detach \
	--net=host \
	--name calico-etcd quay.io/coreos/etcd:v2.3.6 \
	--advertise-client-urls "http://$(LOCAL_IP_ENV):2379,http://127.0.0.1:2379" \
	--listen-client-urls "http://0.0.0.0:2379"

calico_node/.calico_node.created: $(NODE_CONTAINER_FILES)
	cd calico_node && docker build -t calico/node:latest .
	touch calico_node/.calico_node.created

## Display this help text
help: # Some kind of magic from https://gist.github.com/rcmachado/af3db315e31383502660
	$(info Available targets)
	@awk '/^[a-zA-Z\-\_0-9]+:/ {                                   \
		nb = sub( /^## /, "", helpMsg );                             \
		if(nb == 0) {                                                \
			helpMsg = $$0;                                             \
			nb = sub( /^[^:]*:.* ## /, "", helpMsg );                  \
		}                                                            \
		if (nb)                                                      \
			printf "\033[1;31m%-" width "s\033[0m %s\n", $$1, helpMsg; \
	}                                                              \
	{ helpMsg = $$0 }'                                             \
	width=$$(grep -o '^[a-zA-Z_0-9]\+:' $(MAKEFILE_LIST) | wc -L)  \
	$(MAKEFILE_LIST)

# Install or update the tools used by the build
.PHONY: update-tools
update-tools:
	go get -u github.com/Masterminds/glide
	go get -u github.com/onsi/ginkgo/ginkgo
