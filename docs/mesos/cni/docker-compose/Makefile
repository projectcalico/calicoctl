CALICO_NODE_VERSION=v0.19.0
DOCKER_COMPOSE_URL=https://github.com/docker/compose/releases/download/1.4.0/docker-compose-`uname -s`-`uname -m`

default: images

docker-compose:
	  curl -L ${DOCKER_COMPOSE_URL} > docker-compose
	  chmod +x ./docker-compose

calico-node: calico/calico-node-$(CALICO_NODE_VERSION).tar

calico/calico-node-$(CALICO_NODE_VERSION).tar:
	docker pull calico/node:$(CALICO_NODE_VERSION)
	docker save -o calico/calico-node-$(CALICO_NODE_VERSION).tar calico/node:$(CALICO_NODE_VERSION)

images: calico-node docker-compose
	  ./docker-compose pull
	  ./docker-compose build

clean:
	./docker-compose kill
	./docker-compose rm --force

cluster: images
	./docker-compose up -d
	./docker-compose scale slave=3

test-cni:
	docker exec dockercompose_slave_1 mesos-execute --containerizer=mesos --docker_image=busybox --name=cni --master=172.17.0.4:5050 --networks=calico-net-1 --command=ifconfig
