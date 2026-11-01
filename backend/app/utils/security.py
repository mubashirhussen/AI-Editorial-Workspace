import ipaddress
import socket
import re
from urllib.parse import urlparse
from typing import Optional
from fastapi import HTTPException

# Disallowed hostnames and reserved suffixes
BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "instance-data",
    "metadata",
    "169.254.169.254",
    "100.100.100.200", # Alibaba metadata
}

BLOCKED_SUFFIXES = (
    ".local",
    ".internal",
    ".localhost",
    ".lan",
    ".corp",
    ".home.arpa"
)

# Additional reserved / unroutable IP subnets not always covered by is_private in older Python
ADDITIONAL_BLOCKED_NETWORKS = [
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT (RFC 6598)
    ipaddress.ip_network("192.0.0.0/24"),     # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1 (RFC 5737)
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32")# Limited Broadcast
]

def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Verifies whether an IP address belongs to any private, loopback, or cloud internal network."""
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True

    # Cloud metadata explicit IP
    if str(ip) in ("169.254.169.254", "100.100.100.200"):
        return True

    for net in ADDITIONAL_BLOCKED_NETWORKS:
        if ip in net:
            return True

    return False

def is_safe_url(url: str) -> bool:
    """
    Validates that a URL is http/https and does not resolve to private/loopback/internal IPs (SSRF protection).
    Protects against DNS rebinding, octal/hex encodings, and cloud metadata access.
    """
    if not url or not isinstance(url, str):
        return False

    url_clean = url.strip()
    try:
        parsed = urlparse(url_clean)
        # 1. Scheme enforcement
        if parsed.scheme.lower() not in ("http", "https"):
            return False

        # 2. Reject credentials in URL (user:pass@host)
        if parsed.username or parsed.password:
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        hostname_lower = hostname.lower().strip("[]")

        # 3. Hostname blocklist
        if hostname_lower in BLOCKED_HOSTS or any(hostname_lower.endswith(sfx) for sfx in BLOCKED_SUFFIXES):
            return False

        # 4. Check if hostname is an encoded or raw IP representation
        # Handle octal, hex, decimal integers (e.g., 2130706433 = 127.0.0.1)
        if re.match(r"^\d+$", hostname_lower):
            try:
                ip_from_int = ipaddress.ip_address(int(hostname_lower))
                if is_ip_blocked(ip_from_int):
                    return False
            except ValueError:
                return False

        try:
            direct_ip = ipaddress.ip_address(hostname_lower)
            if is_ip_blocked(direct_ip):
                return False
        except ValueError:
            pass

        # 5. DNS Resolution check (prevent DNS rebinding to internal subnets)
        try:
            addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
            if not addr_info:
                return False

            for item in addr_info:
                ip_str = item[4][0]
                resolved_ip = ipaddress.ip_address(ip_str)
                if is_ip_blocked(resolved_ip):
                    return False
        except (socket.gaierror, socket.herror, ValueError):
            return False

        return True
    except Exception:
        return False

def validate_url_safe(url: str):
    """Raises HTTPException if URL fails SSRF safety checks."""
    if not is_safe_url(url):
        raise HTTPException(
            status_code=400,
            detail="Security violation: Access to localhost, private IP subnets, or internal addresses is blocked."
        )
