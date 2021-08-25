from __future__ import annotations

import ipaddress
import pathlib
import ssl
from datetime import timedelta, datetime
from io import BytesIO
from typing import cast, TYPE_CHECKING, Optional, Iterable, Union, Any, List

from glQiwiApi.ext.exceptions import StateError

if TYPE_CHECKING:
    try:
        from aiogram.types import InputFile  # NOQA
        from cryptography import x509  # NOQA
        from cryptography.hazmat.primitives.asymmetric.rsa import (
            RSAPrivateKeyWithSerialization,  # NOQA
        )  # NOQA
    except ImportError:  # pragma: no cover # type: ignore
        pass


class SSLConfigurator:
    """
    Help you to generate self-signed certificate and load it as ssl.SSLContext
    Firstly, install `cryptography` package => pip install cryptography or poetry add cryptography

    """

    def __init__(
        self,
        hostname: str,  # your host machine ip address
        cert_path: Union[str, pathlib.Path] = "cert.pem",
        pkey_path: Union[str, pathlib.Path] = "pkey.pem",
        ip_addresses: Optional[Iterable[Any]] = None,
        rsa_private_key: Optional["RSAPrivateKeyWithSerialization"] = None,
        public_exponent: int = 65537,
        key_size: int = 2048,
        backend: Optional[Any] = None,
        serial_number: int = 1000,
        expire_days: int = 3650,
    ):
        self.expire_days = expire_days
        self.serial_number = serial_number
        self.backend = backend
        self.key_size = key_size
        self.public_exponent = public_exponent
        self._rsa_private_key = rsa_private_key
        self.ip_addresses = ip_addresses
        self.pkey_path = pkey_path
        self.cert_path = cert_path
        self.hostname = hostname

    def as_ssl_context(self) -> "ssl.SSLContext":
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        try:
            ssl_context.load_cert_chain(str(self.cert_path), str(self.pkey_path))
        except FileNotFoundError:
            raise StateError(
                "There are not certificates in folder."
                " Firstly, you need to call "
                "`SSLConfigurator.generate_self_signed` method."
            )
        return ssl_context

    def _get_self_signed_cert(self) -> bool:
        if isinstance(self.cert_path, pathlib.Path):
            is_cert_is_file = self.cert_path.is_file()
        else:
            is_cert_is_file = pathlib.Path(self.cert_path).is_file()

        if isinstance(self.pkey_path, pathlib.Path):
            is_pkey_is_file = self.pkey_path.is_file()
        else:
            is_pkey_is_file = pathlib.Path(self.pkey_path).is_file()

        return is_cert_is_file and is_pkey_is_file

    def get_or_generate_self_signed(
        self, *name_attributes: "x509.NameAttribute"
    ) -> SSLConfigurator:
        """
        Generates self signed certificate for a hostname, and optional IP addresses.
        Copied from https://gist.github.com/bloodearnest/9017111a313777b9cce5
        """
        if self._get_self_signed_cert():
            return self

        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
        except ImportError:
            raise ImportError(
                "You need to pip install cryptography for generating self-signed cert"
            )

        # Generate our key
        if self._rsa_private_key is None:
            self._rsa_private_key = rsa.generate_private_key(
                public_exponent=self.public_exponent,
                key_size=self.key_size,
                backend=self.backend or default_backend(),
            )

        name = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, self.hostname), *name_attributes]
        )

        # best practice seem to be to include the hostname in the SAN,
        # which *SHOULD* mean COMMON_NAME is ignored.
        alt_names: List[x509.GeneralName] = [x509.DNSName(self.hostname)]

        # allow addressing by IP, for when you don't have real DNS (common in most testing scenarios
        if self.ip_addresses:
            for address in self.ip_addresses:
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
            .public_key(self._rsa_private_key.public_key())
            .serial_number(self.serial_number)
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=self.expire_days))
            .add_extension(basic_constraints, False)
            .add_extension(san, False)
            .sign(self._rsa_private_key, hashes.SHA256(), default_backend())
        )
        cert_pem = cert.public_bytes(
            encoding=cast(serialization.Encoding, serialization.Encoding.PEM)
        )
        key_pem = self._rsa_private_key.private_bytes(
            encoding=cast(serialization.Encoding, serialization.Encoding.PEM),
            format=cast(
                serialization.PrivateFormat,
                serialization.PrivateFormat.TraditionalOpenSSL,
            ),
            encryption_algorithm=serialization.NoEncryption(),
        )

        with open(self.cert_path, "wb") as f1, open(self.pkey_path, "wb") as f2:
            f1.write(cert_pem)
            f2.write(key_pem)
        return self

    def as_input_file(self) -> "InputFile":
        from aiogram.types import InputFile

        with open(self.cert_path, "rb") as f:
            return InputFile(BytesIO(f.read()))
