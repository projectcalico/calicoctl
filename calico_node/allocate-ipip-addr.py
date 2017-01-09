# If IPIP is enabled, the host requires an IP address for its tunnel
# device, which is in an IPIP pool.  Without this, a host can't originate
# traffic to a pool address because the response traffic would not be
# routed via the tunnel (likely being dropped by RPF checks in the fabric).
#
# This is a oneshot python script that queries etcd for existing pools.
# If any pool has --ipip, it will ensure this host's tunl0 interface
# has been assigned an IP from the ipip pool.

import os
import socket
import sys
from netaddr import AddrFormatError, IPAddress
from pycalico.ipam import IPAMClient

def _find_pool(ip_addr, ipv4_pools):
    """
    Find the pool containing the given IP.

    :param ip_addr:  IP address to find.
    :param ipv4_pools:  iterable containing IPPools.
    :return: The pool, or None if not found
    """
    for pool in ipv4_pools:
        if ip_addr in pool.cidr:
            return pool
    else:
        return None


def _ensure_host_tunnel_addr(ipv4_pools, ipip_pools):
    """
    Ensure the host has a valid IP address for its IPIP tunnel device.

    This must be an IP address claimed from one of the IPIP pools.
    Handles re-allocating the address if it finds an existing address
    that is not from an IPIP pool.

    :param ipv4_pools: List of all IPv4 pools.
    :param ipip_pools: List of IPIP-enabled pools.
    """
    ip_addr = _get_host_tunnel_ip()
    if ip_addr:
        # Host already has a tunnel IP assigned, verify that it's still valid.
        pool = _find_pool(ip_addr, ipv4_pools)
        if pool and not pool.ipip:
            # No longer an IPIP pool. Release the IP, it's no good to us.
            client.release_ips({ip_addr})
            ip_addr = None
        elif not pool:
            # Not in any IPIP pool.  IP must be stale.  Since it's not in any
            # pool, we can't release it.
            ip_addr = None
    if not ip_addr:
        # Either there was no IP or the IP needs to be replaced.  Try to
        # get an IP from one of the IPIP-enabled pools.
        _assign_host_tunnel_addr(ipip_pools)


def _assign_host_tunnel_addr(ipip_pools):
    """
    Claims an IPIP-enabled IP address from the first pool with some
    space.

    Stores the result in the host's config as its tunnel address.

    Exits on failure.
    :param ipip_pools:  List of IPPools to search for an address.
    """
    for ipip_pool in ipip_pools:
        v4_addrs, _ = client.auto_assign_ips(
            num_v4=1, num_v6=0,
            handle_id=None,
            attributes={},
            pool=(ipip_pool, None),
            host=nodename
        )
        if v4_addrs:
            # Successfully allocated an address.  Unpack the list.
            [ip_addr] = v4_addrs
            break
    else:
        # Failed to allocate an address, the pools must be full.
        print "Failed to allocate an IP address from an IPIP-enabled pool " \
            "for the host's IPIP tunnel device.  Pools are likely " \
            "exhausted."

        sys.exit(1)
    # If we get here, we've allocated a new IPIP-enabled address,
    # Store it in etcd so that Felix will pick it up.
    client.set_per_host_config(nodename, "IpInIpTunnelAddr",
                               str(ip_addr))


def _remove_host_tunnel_addr():
    """
    Remove any existing IP address for this host's IPIP tunnel device.

    Idempotent; does nothing if there is no IP assigned.  Releases the
    IP from IPAM.
    """
    ip_addr = _get_host_tunnel_ip()
    if ip_addr:
        client.release_ips({ip_addr})
    client.remove_per_host_config(nodename, "IpInIpTunnelAddr")


def _get_host_tunnel_ip():
    """
    :return: The IPAddress of the host's IPIP tunnel or None if not
             present/invalid.
    """
    raw_addr = client.get_per_host_config(nodename, "IpInIpTunnelAddr")
    try:
        ip_addr = IPAddress(raw_addr)
    except (AddrFormatError, ValueError, TypeError):
        # Either there's no address or the data is bad.  Treat as missing.
        ip_addr = None
    return ip_addr


def main():
    # If we're running with the k8s backend, don't do any of this,
    # since it currently doesn't support BGP, Calico IPAM, and doesn't
    # require any of the etcd interactions below.
    if os.getenv("DATASTORE_TYPE", "") == "kubernetes":
        return

    ipv4_pools = client.get_ip_pools(4)
    ipip_pools = [p for p in ipv4_pools if p.ipip]

    if ipip_pools:
        # IPIP is enabled, make sure the host has an address for its tunnel.
        _ensure_host_tunnel_addr(ipv4_pools, ipip_pools)
    else:
        # No IPIP pools, clean up any old address.
        _remove_host_tunnel_addr()


# Try the NODENAME (preferentially) or nodename environment variable, but
# default to the socket.getnodename() value if unset.
nodename = os.getenv("NODENAME") or os.getenv("HOSTNAME")
if not nodename:
    nodename = socket.gethostname()
client = IPAMClient()

if __name__ == "__main__":
    main()
