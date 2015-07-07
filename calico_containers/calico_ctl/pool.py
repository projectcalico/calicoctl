"""
Configure IP Pools

Usage:
  calicoctl pool (add|remove) <CIDR> [--ipip] [--nat-outgoing]
  calicoctl pool show [--ipv4 | --ipv6]

Options:
 --ipv4                   Show IPv4 information only.
 --ipv6                   Show IPv6 information only.
 """
import sys
from pycalico.datastore_datatypes import IPPool
from utils import get_container_ipv_from_arguments
from utils import client
from utils import check_ip_version
from netaddr import IPNetwork
from prettytable import PrettyTable


def pool(arguments):
    ip_version = get_container_ipv_from_arguments(arguments)
    if arguments.get("pool"):
        if arguments.get("add"):
            ip_pool_add(arguments.get("<CIDR>"),
                        ip_version,
                        arguments.get("--ipip"),
                        arguments.get("--nat-outgoing"))
        elif arguments.get("remove"):
            ip_pool_remove(arguments.get("<CIDR>"), ip_version)
        elif arguments.get("show"):
            if not ip_version:
                ip_pool_show("v4")
                ip_pool_show("v6")
            else:
                ip_pool_show(ip_version)


def ip_pool_add(cidr_pool, version, ipip, masquerade):
    """
    Add the the given CIDR range to the IP address allocation pool.

    :param cidr_pool: The pool to set in CIDR format, e.g. 192.168.0.0/16
    :param version: v4 or v6
    :param ipip: Use IP in IP for this pool.
    :return: None
    """
    if version == "v6" and ipip:
        print "IP in IP not supported for IPv6 pools"
        sys.exit(1)

    cidr = check_ip_version(cidr_pool, version, IPNetwork)
    pool = IPPool(cidr, ipip=ipip, masquerade=masquerade)
    client.add_ip_pool(version, pool)


def ip_pool_remove(cidr_pool, version):
    """
    Add the the given CIDR range to the IP address allocation pool.

    :param cidr_pool: The pool to set in CIDR format, e.g. 192.168.0.0/16
    :param version: v4 or v6
    :return: None
    """
    cidr = check_ip_version(cidr_pool, version, IPNetwork)
    try:
        client.remove_ip_pool(version, cidr)
    except KeyError:
        print "%s is not a configured pool." % cidr_pool


def ip_pool_show(version):
    """
    Print a list of IP allocation pools.
    :return: None
    """
    assert version in ("v4", "v6")
    headings = ["IP%s CIDR" % version, "Options"]
    pools = client.get_ip_pools(version)
    x = PrettyTable(headings)
    for pool in pools:
        enabled_options = []
        if version == "v4":
            if pool.ipip:
                enabled_options.append("ipip")
            if pool.masquerade:
                enabled_options.append("nat-outgoing")
        # convert option array to string
        row = [str(pool.cidr), ','.join(enabled_options)]
        x.add_row(row)
    print x.get_string(sortby=headings[0])
