#!/usr/bin/env python

import argparse
from docker import Client


def setup_parser():
    p = argparse.ArgumentParser(prog='container-status',
                                description='Return the ID of running containers'
                                            ' on a live system')
    p.add_argument('-t','--tag', required=True,
                   help='Docker tag to apply to the build')
    return p

def find_running_container(cli, tag):
    containers = cli.containers()
    for c in containers:
        for name in c['Names']:
            if tag in name:
                return c['Id']


def main(args=None):
    parser = setup_parser()
    known, unknown = parser.parse_known_args(args)

    cli = Client(base_url='unix://var/run/docker.sock')

    running_container = find_running_container(cli, known.tag)

    if running_container:
        print running_container

if __name__ == "__main__":
    main()
