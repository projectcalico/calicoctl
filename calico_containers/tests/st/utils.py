import sh
from sh import docker, ErrorReturnCode_127, ErrorReturnCode_255
import socket
from time import sleep


def get_ip():
    """Return a string of the IP of the hosts eth0 interface."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def delete_container(name):
    """
    Cleanly delete a container.
    """
    # We *must* remove all inner containers and images before removing the outer
    # container. Otherwise the inner images will stick around and fill disk.
    # https://github.com/jpetazzo/dind#important-warning-about-disk-usage
    cleanup_inside(name)
    sh.docker.rm("-f", name, _ok_code=[0, 1])


def cleanup_inside(name):
    """
    Clean the inside of a container by deleting the containers and images within it.
    """
    cleanup_inner_containers(name)
    cleanup_inner_images(name)


def cleanup_inner_containers(name):
    try:
        inner_containers = docker("exec", "-t", name, "bash", "-c", "docker ps -qa").stdout.split()
    except ErrorReturnCode_255:
        # 255 caused by '"bash": executable file not found in $PATH'
        # This happens in the etcd container.
        pass
    else:
        for container in inner_containers:
            docker("exec", "-t", name, "bash", "-c", "docker rm -f %s" % container)


def cleanup_inner_images(name):
    try:
        inner_images = docker("exec", "-t", name, "bash", "-c", "docker images -q").stdout.split()
    except ErrorReturnCode_255:
        # 255 caused by '"bash": executable file not found in $PATH'
        # This happens in the etcd container.
        pass
    else:
        for image in inner_images:
            docker("exec", "-t", name, "bash", "-c", "docker rmi %s" % image)


def retry_until_success(function, retries=10, ex_class=Exception):
    """
    Retries function until no exception is thrown. If exception continues,
    it is reraised.

    :param function: the function to be repeatedly called
    :param retries: the maximum number of times to retry the function.
    A value of 0 will run the function once with no retries.
    :param ex_class: The class of expected exceptions.
    :returns: the value returned by function
    """
    for retry in range(retries + 1):
        try:
            result = function()
        except ex_class:
            if retry < retries:
                sleep(1)
            else:
                raise
        else:
            # Successfully ran the function
            return result
