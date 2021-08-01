from __future__ import annotations

import ipaddress

from glQiwiApi.core.dispatcher.webhooks.config import ALLOWED_IPS


def check_ip(ip_address: str) -> bool:
    """
    Check if ip is allowed to request us

    :param ip_address: IP-address
    :return: address is allowed
    """
    address = ipaddress.IPv4Address(ip_address)
    unpacked = [ip_address for pool in ALLOWED_IPS for ip_address in pool]
    return address in unpacked
