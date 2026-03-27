"""
Utility functions for passkey (WebAuthn) configuration.
"""

import os
import ipaddress
from flask import request


def normalize_passkey_host(hostname: str) -> str:
    """
    Normalize and validate a hostname for WebAuthn (RP ID usage).

    Ensures the hostname is:
    - 'localhost', or
    - a valid fully qualified domain name (FQDN)

    Converts loopback IPs to 'localhost' and rejects unsupported formats.

    Args:
        hostname (str): The hostname to validate.

    Returns:
        str: A normalized hostname suitable as RP ID.

    Raises:
        ValueError: If the hostname is invalid for passkey usage.
    """

    host = (hostname or "").strip().lower().strip("[]")

    if not host:
        raise ValueError("Unable to determine the current hostname for passkey login.")

    if host == "localhost":
        return host

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip:
        if ip.is_loopback or ip.is_unspecified:
            return "localhost"
        raise ValueError("Passkeys require a domain name. Use localhost locally or serve the app from your HTTPS domain.")

    if "." not in host:
        raise ValueError("Passkeys require localhost or a fully qualified domain name.")

    return host


def get_passkey_rp_id() -> str:
    """
    Determine the relying party ID (RP ID) for WebAuthn.

    Uses the configured PASSKEY_RP_ID if provided, otherwise derives it
    from the current request hostname.

    Returns:
        str: A valid RP ID for passkey operations.
    """

    configured_rp_id = (os.environ.get("PASSKEY_RP_ID") or "").strip()

    if configured_rp_id:
        return normalize_passkey_host(configured_rp_id)

    return normalize_passkey_host(request.host.split(":", 1)[0])