.PHONY: all binary test ut vendor node_image force test-containerized

BUILD_CONTAINER_NAME=calico/calicoctl_build_container
BUILD_CONTAINER_MARKER=calicoctl_build_container.created

NODE_CONTAINER_DIR=calico_node
NODE_CONTAINER_FILES=$(shell find calico_node/ -type f ! -name '*.created')

default: binary node_image
all: test
test: ut

vendor:
	glide up

binary: dist/calicoctl

ut: binary
	./run-uts

st:
	true

semaphore: st

force:
	true

dist/calicoctl: force
	mkdir -p dist
	go build -o dist/calicoctl "./calicoctl/calicoctl.go"

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
	-p 2379:2379 \
	--name calico-etcd quay.io/coreos/etcd:v2.3.6 \
	--advertise-client-urls "http://127.0.0.1:2379,http://127.0.0.1:4001" \
	--listen-client-urls "http://0.0.0.0:2379,http://0.0.0.0:4001"

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
