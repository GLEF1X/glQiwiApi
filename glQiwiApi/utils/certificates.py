from __future__ import annotations

import ipaddress
import pathlib
import ssl
from dataclasses import dataclass
from datetime import timedelta, datetime
from io import BytesIO
from os import PathLike
from typing import cast, TYPE_CHECKING, Optional, Iterable, Any, List, Union

if TYPE_CHECKING:
    try:
        from cryptography import x509  # NOQA
        from cryptography.hazmat.primitives.asymmetric.rsa import (
            RSAPrivateKeyWithSerialization,  # NOQA
        )  # NOQA
    except ImportError:
        pass

try:
    from aiogram.types import InputFile  # NOQA
except ImportError:
    pass


@dataclass
class SSLCertificate:
    _cert_path: Union[str, PathLike]
    _pkey_path: Union[str, PathLike]

    def as_ssl_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(self._cert_path, self._pkey_path)
        return context

    def as_input_file(self) -> "InputFile":
        with open(self._cert_path, "rb") as file:
            return InputFile(BytesIO(file.read()))


def get_or_generate_self_signed_certificate(hostname: str,  # your host machine ip address
                                            cert_path: Union[str, PathLike] = "cert.pem",
                                            pkey_path: Union[str, PathLike] = "pkey.pem",
                                            ip_addresses: Optional[Iterable[Any]] = None,
                                            rsa_private_key: Optional[
                                                "RSAPrivateKeyWithSerialization"] = None,
                                            public_exponent: int = 65537,
                                            key_size: int = 2048,
                                            backend: Optional[Any] = None,
                                            serial_number: int = 1000,
                                            expire_days: int = 3650,
                                            *name_attributes: "x509.NameAttribute") -> SSLCertificate:
    """
    Generates self signed certificate for a hostname, and optional IP addresses.

    Copied from https://gist.github.com/bloodearnest/9017111a313777b9cce5
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        raise ImportError("You need to install cryptography package for generating self-signed cert")

    if pathlib.Path(cert_path).is_file() and pathlib.Path(pkey_path).is_file():
        return SSLCertificate(_cert_path=cert_path, _pkey_path=pkey_path)

    # Generate our key
    if rsa_private_key is None:
        rsa_private_key = rsa.generate_private_key(
            public_exponent=public_exponent,
            key_size=key_size,
            backend=backend or default_backend(),
        )

    name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, hostname), *name_attributes]
    )

    # best practice seem to be to include the hostname in the SAN,
    # which *SHOULD* mean COMMON_NAME is ignored.
    alt_names: List[x509.GeneralName] = [x509.DNSName(hostname)]

    # allow addressing by IP, for when you don't have real DNS (common in most testing scenarios
    if ip_addresses:
        for address in ip_addresses:
            # openssl wants DNSnames for ips...
            alt_names.append(x509.DNSName(address))
            # ... whereas golang's crypto/tls is stricter, and needs IPAddresses
            # note: older versions of cryptography do not understand ip_address objects
            alt_names.append(x509.IPAddress(ipaddress.ip_address(address)))

    san = x509.SubjectAlternativeName(alt_names)

    # path_len=0 means this cert can only sign itself, not other certs.
    basic_constraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(rsa_private_key.public_key())
            .serial_number(serial_number)
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=expire_days))
            .add_extension(basic_constraints, False)
            .add_extension(san, False)
            .sign(rsa_private_key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(
        encoding=cast(serialization.Encoding, serialization.Encoding.PEM)
    )
    key_pem = rsa_private_key.private_bytes(
        encoding=cast(serialization.Encoding, serialization.Encoding.PEM),
        format=cast(
            serialization.PrivateFormat,
            serialization.PrivateFormat.TraditionalOpenSSL,
        ),
        encryption_algorithm=serialization.NoEncryption(),
    )

    with open(cert_path, "wb+") as f1, open(pkey_path, "wb") as f2:
        f1.write(cert_pem)
        f2.write(key_pem)
    return SSLCertificate(_cert_path=cert_path, _pkey_path=pkey_path)
