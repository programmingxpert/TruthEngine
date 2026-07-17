"""Security validations and SSRF prevention utilities."""

import ipaddress
import socket
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Normalize a URL to a canonical format, stripping fragments and default ports."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path
    if path.endswith("/") and path != "/":
        path = path[:-1]
    if not path:
        path = "/"

    query = parsed.query
    query_str = f"?{query}" if query else ""

    return f"{scheme}://{netloc}{path}{query_str}"


def validate_dns_ip(host: str) -> str:
    """Resolve DNS for the host and raise ValueError if it points to a private/unsafe IP."""
    try:
        addrinfo = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        msg = f"DNS resolution failed for host {host}"
        raise ValueError(msg) from exc

    for _family, _type, _proto, _canonname, sockaddr in addrinfo:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError as exc:
            msg = f"Invalid IP address resolved: {ip_str}"
            raise ValueError(msg) from exc

        if ip.is_loopback:
            msg = f"Host resolves to loopback IP: {ip_str}"
            raise ValueError(msg)
        if ip.is_link_local:
            msg = f"Host resolves to link-local IP: {ip_str}"
            raise ValueError(msg)
        if ip.is_private:
            msg = f"Host resolves to private IP range: {ip_str}"
            raise ValueError(msg)
        if ip.is_multicast:
            msg = f"Host resolves to multicast IP: {ip_str}"
            raise ValueError(msg)
        if ip.is_unspecified:
            msg = f"Host resolves to unspecified IP: {ip_str}"
            raise ValueError(msg)

        if isinstance(ip, ipaddress.IPv6Address):
            ipv4_mapped = ip.ipv4_mapped
            if ipv4_mapped is not None:
                if ipv4_mapped.is_loopback or ipv4_mapped.is_private or ipv4_mapped.is_link_local:
                    msg = f"Host resolves to private/loopback IPv4-mapped IP: {ip_str}"
                    raise ValueError(msg)

    return str(addrinfo[0][4][0])
