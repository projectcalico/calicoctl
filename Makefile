.PHONY: *

rkt:
	# Build docker container
	cd build_calicoctl; docker build -t calico-build .
	mkdir -p dist
	chmod 777 `pwd`/dist
	# Build the rkt plugin
	docker run -u user -v `pwd`/calico_containers/integrations/rkt:/calico -v `pwd`/dist:/code/dist calico-build pyinstaller /calico/calico_rkt.py -a -F -s --clean

clean:
	rm -rf dist
