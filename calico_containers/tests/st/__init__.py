import os
import sh
from sh import docker


def setup_package():
    """
    Sets up docker images and host containers for running the STs.
    """
    if "SEMAPHORE_CACHE_DIR" in os.environ:
        tar_dir = os.environ["SEMAPHORE_CACHE_DIR"]
    else:
        tar_dir = os.path.abspath('.')
    # Pull and save each image, so we can use them inside the host containers.
    print sh.bash("./build_node.sh").stdout
    docker.save("--output", os.path.join(tar_dir, "calico-node.tar"), "calico/node")
    if not os.path.isfile(os.path.join(tar_dir, "busybox.tar")):
        docker.pull("busybox:latest")
        docker.save("--output", os.path.join(tar_dir, "busybox.tar"), "busybox:latest")
    if not os.path.isfile(os.path.join(tar_dir, "nsenter.tar")):
        docker.pull("jpetazzo/nsenter:latest")
        docker.save("--output", os.path.join(tar_dir, "nsenter.tar"), "jpetazzo/nsenter:latest")
    if not os.path.isfile(os.path.join(tar_dir, "etcd.tar")):
        docker.pull("quay.io/coreos/etcd:v2.0.10")
        docker.save("--output", os.path.join(tar_dir, "etcd.tar"), "quay.io/coreos/etcd:v2.0.10")

    # Create the calicoctl binary here so it will be in the volume mounted on the hosts.
    print sh.bash("./create_binary.sh")
    print "Calicoctl binary created."


def teardown_package():
    pass
