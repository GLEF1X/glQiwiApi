import uuid

import pytest

from glQiwiApi import QiwiP2PClient
from glQiwiApi.qiwi.clients.p2p.client import NoShimUrlWasProvidedError
from glQiwiApi.utils.compat import remove_suffix


def test_old_style_deprecation_warn():
    old_style_shim_url = 'https://example.com/proxy/p2p/{0}'

    expected_warn_message = (
        'Old-style urls that were used like format-like strings are deprecated '
    )
    f"use plain path like this - {remove_suffix(old_style_shim_url, '{0}')} instead."

    with pytest.warns(DeprecationWarning, match=expected_warn_message):
        _ = QiwiP2PClient(secret_p2p='fake secret p2p', shim_server_url=old_style_shim_url)


def test_strip_format_variable_when_old_style_url_passed():
    old_style_shim_url = 'https://example.com/proxy/p2p/{0}'

    c = QiwiP2PClient(secret_p2p='fake secret p2p', shim_server_url=old_style_shim_url)

    assert c._shim_server_url == 'https://example.com/proxy/p2p/'


def test_create_shim_url():
    c = QiwiP2PClient(
        secret_p2p='fake secret p2p', shim_server_url='https://example.com/proxy/p2p/'
    )

    random_uuid = str(uuid.uuid4())

    assert c.create_shim_url(random_uuid) == f'https://example.com/proxy/p2p/{random_uuid}'


def test_create_shim_url_with_old_style_urls():
    c = QiwiP2PClient(
        secret_p2p='fake secret p2p', shim_server_url='https://example.com/proxy/p2p/{0}'
    )

    random_uuid = str(uuid.uuid4())

    assert c.create_shim_url(random_uuid) == f'https://example.com/proxy/p2p/{random_uuid}'


def test_raise_when_shim_url_is_None():
    c = QiwiP2PClient(secret_p2p='fake secret p2p')

    with pytest.raises(NoShimUrlWasProvidedError):
        c.create_shim_url(str(uuid.uuid4()))
