import ssl

from py.path import local

from glQiwiApi.utils.certificates import get_or_generate_self_signed_certificate


def test_generate_self_signed_certificates(tmpdir: local):
    tmpdir.mkdir("certificates")
    path_to_cert = tmpdir.join("cert.pem")
    path_to_pkey = tmpdir.join("pkey.pem")
    get_or_generate_self_signed_certificate(
        hostname="45.138.24.80", cert_path=path_to_cert, pkey_path=path_to_pkey
    )
    assert path_to_cert.isfile() is True
    assert path_to_pkey.isfile() is True


def test_get_ssl_context(tmpdir: local):
    tmpdir.mkdir("certificates")
    ssl_certificate = get_or_generate_self_signed_certificate(
        hostname="45.138.24.80",
        cert_path=tmpdir.join("cert.pem"),
        pkey_path=tmpdir.join("pkey.pem"),
    )
    context = ssl_certificate.as_ssl_context()
    assert isinstance(context, ssl.SSLContext)


def test_get_input_file(tmpdir: local):
    tmpdir.mkdir("certificates")
    ssl_certificate = get_or_generate_self_signed_certificate(
        hostname="45.138.24.80",
        cert_path=tmpdir.join("cert.pem"),
        pkey_path=tmpdir.join("pkey.pem"),
    )
    input_file = ssl_certificate.as_input_file()
    assert input_file.get_file().read() == tmpdir.join("cert.pem").read().encode("utf-8")
