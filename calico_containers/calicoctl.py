#!/usr/bin/env python

# Copyright 2015 Metaswitch Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""calicoctl

Override the host:port of the ETCD server by setting the environment variable
ETCD_AUTHORITY [default: 127.0.0.1:4001]

Usage: calicoctl <command> [<args>...]

    status            Print current status information
    node              Configure the main calico/node container and establish Calico networking
    container         Configure containers and their addresses
    profile           Configure endpoint profiles
    endpoint          Configure the endpoints assigned to existing containers
    pool              Configure ip-pools
    bgp               Configure global bgp
    checksystem       Check for incompatabilities on the host system
    diags             Save diagnostic information

See 'calicoctl <command> --help' to read about a specific subcommand.
"""
import sys
import traceback
import netaddr
from netaddr import AddrFormatError
import re
from urllib3.exceptions import MaxRetryError
from docopt import docopt
from requests.exceptions import ConnectionError
from pycalico.datastore_errors import DataStoreError


import calico_ctl.node
import calico_ctl.container
import calico_ctl.profile
import calico_ctl.endpoint
import calico_ctl.pool
import calico_ctl.bgp
import calico_ctl.checksystem
import calico_ctl.status
import calico_ctl.diags
from calico_ctl.utils import print_paragraph


def permission_denied_error(conn_error):
    """
    Determine whether the supplied connection error is from a permission denied
    error.
    :param conn_error: A requests.exceptions.ConnectionError instance
    :return: True if error is from permission denied.
    """
    # Grab the MaxRetryError from the ConnectionError arguments.
    mre = None
    for arg in conn_error.args:
        if isinstance(arg, MaxRetryError):
            mre = arg
            break
    if not mre:
        return None

    # See if permission denied is in the MaxRetryError arguments.
    se = None
    for arg in mre.args:
        if "Permission denied" in str(arg):
            se = arg
            break
    if not se:
        return None

    return True


def validate_arguments(arguments):
        """
        Validate common argument values.

        :param arguments: Docopt processed arguments.
        """
        # List of valid characters that Felix permits
        valid_chars = '[a-zA-Z0-9_\.\-]'

        # Validate Profiles
        profile_ok = True
        if "<PROFILES>" in arguments or "<PROFILE>" in arguments:
            profiles = arguments.get("<PROFILES>") or arguments.get("<PROFILE>")
            if profiles:
                for profile in profiles:
                    if not re.match("^%s+$" % valid_chars, profile):
                        profile_ok = False
                        break

        # Validate tags
        tag_ok = (arguments.get("<TAG>") is None or
                  re.match("^%s+$" % valid_chars, arguments["<TAG>"]))

        # Validate IPs
        ip_ok = arguments.get("--ip") is None or netaddr.valid_ipv4(arguments.get("--ip"))
        ip6_ok = arguments.get("--ip6") is None or \
                 netaddr.valid_ipv6(arguments.get("--ip6"))
        container_ip_ok = arguments.get("<IP>") is None or \
                          netaddr.valid_ipv4(arguments["<IP>"]) or \
                          netaddr.valid_ipv6(arguments["<IP>"])
        peer_ip_ok = arguments.get("<PEER_IP>") is None or \
                     netaddr.valid_ipv4(arguments["<PEER_IP>"]) or \
                     netaddr.valid_ipv6(arguments["<PEER_IP>"])
        cidr_ok = True
        for arg in ["<CIDR>", "<SRCCIDR>", "<DSTCIDR>"]:
            if arguments.get(arg):
                try:
                    arguments[arg] = str(netaddr.IPNetwork(arguments[arg]))
                except (AddrFormatError, ValueError):
                    # Some versions of Netaddr have a bug causing them to return a
                    # ValueError rather than an AddrFormatError, so catch both.
                    cidr_ok = False
        icmp_ok = True
        for arg in ["<ICMPCODE>", "<ICMPTYPE>"]:
            if arguments.get(arg) is not None:
                try:
                    value = int(arguments[arg])
                    if not (0 <= value < 255):  # Felix doesn't support 255
                        raise ValueError("Invalid %s: %s" % (arg, value))
                except ValueError:
                    icmp_ok = False
        asnum_ok = True
        if arguments.get("<AS_NUM>") or arguments.get("--as"):
            try:
                asnum = int(arguments["<AS_NUM>"] or arguments["--as"])
                asnum_ok = 0 <= asnum <= 4294967295
            except ValueError:
                asnum_ok = False

        if not profile_ok:
            print_paragraph("Profile names must be < 40 character long and can "
                            "only contain numbers, letters, dots, dashes and "
                            "underscores.")
        if not tag_ok:
            print_paragraph("Tags names can only contain numbers, letters, dots, "
                            "dashes and underscores.")
        if not ip_ok:
            print "Invalid IPv4 address specified with --ip argument."
        if not ip6_ok:
            print "Invalid IPv6 address specified with --ip6 argument."
        if not container_ip_ok or not peer_ip_ok:
            print "Invalid IP address specified."
        if not cidr_ok:
            print "Invalid CIDR specified."
        if not icmp_ok:
            print "Invalid ICMP type or code specified."
        if not asnum_ok:
            print "Invalid AS Number specified."

        if not (profile_ok and ip_ok and ip6_ok and tag_ok and peer_ip_ok and
                    container_ip_ok and cidr_ok and icmp_ok and asnum_ok):
            sys.exit(1)


if __name__ == '__main__':
    # TODO: come up with a better way to default to --help when no opts provided
    if len(sys.argv) == 1:
        sys.argv.append('--help')

    # Run command through initial docopt processing to determine subcommand
    command_args = docopt(__doc__, options_first=True)

    # Group the additional args together and forward them along
    argv = [command_args['<command>']] + command_args['<args>']

    # Dispatch the appropriate subcommand
    try:
        command = command_args['<command>']
        if command == 'node':
            # Run the program's argvs through the submodules docopt
            arguments = docopt(calico_ctl.node.__doc__, argv=argv)
            # Validate the arguments
            validate_arguments(arguments)
            # Call the function dispatcher
            calico_ctl.node.node(arguments)
        elif command == 'container':
            arguments = docopt(calico_ctl.container.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.container.container(arguments)
        elif command == 'profile':
            arguments = docopt(calico_ctl.profile.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.profile.profile(arguments)
        elif command == 'endpoint':
            arguments = docopt(calico_ctl.endpoint.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.endpoint.endpoint(arguments)
        elif command == 'pool':
            arguments = docopt(calico_ctl.pool.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.pool.pool(arguments)
        elif command == 'bgp':
            arguments = docopt(calico_ctl.bgp.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.bgp.bgp(arguments)
        elif command == 'checksystem':
            arguments = docopt(calico_ctl.checksystem.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.checksystem.checksystem(arguments)
        elif command == 'status':
            arguments = docopt(calico_ctl.status.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.status.status(arguments)
        elif command == 'diags':
            arguments = docopt(calico_ctl.diags.__doc__, argv=argv)
            validate_arguments(arguments)
            calico_ctl.diags.diags(arguments)
    except SystemExit:
        raise
    except ConnectionError as e:
        # We hit a "Permission denied error (13) if the docker daemon
        # does not have sudo permissions
        if permission_denied_error(e):
            print_paragraph("Unable to run command.  Re-run the "
                            "command as root, or configure the docker "
                            "group to run with sudo privileges (see docker "
                            "installation guide for details).")
        else:
            print_paragraph("Unable to run docker commands. Is the docker "
                            "daemon running?")
        sys.exit(1)
    except DataStoreError as e:
        print_paragraph(e.message)
        sys.exit(1)
    except BaseException as e:
        print "Unexpected error executing command.\n"
        traceback.print_exc()
        sys.exit(1)
