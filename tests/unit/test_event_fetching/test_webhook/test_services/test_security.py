from ipaddress import IPv4Address, IPv4Network

import pytest

from glQiwiApi.core.event_fetching.webhooks.services.security.ip import IPFilter


class TestSecurity:
    def test_empty_init(self):
        ip_filter = IPFilter()
        assert not ip_filter._allowed_ips

    @pytest.mark.parametrize(
        'ip,result',
        [
            ('127.0.0.1', True),
            ('127.0.0.2', False),
            (IPv4Address('127.0.0.1'), True),
            (IPv4Address('127.0.0.2'), False),
            (IPv4Address('91.213.51.3'), True),
            ('192.168.0.33', False),
            ('91.213.51.5', True),
            ('91.213.51.8', True),
            ('10.111.1.100', False),
        ],
    )
    def test_check_ip(self, ip, result):
        ip_filter = IPFilter(
            ips=['127.0.0.1', IPv4Address('91.213.51.3'), IPv4Network('91.213.51.0/24')]
        )
        assert (ip in ip_filter) is result

    def test_default(self):
        ip_filter = IPFilter.default()
        assert isinstance(ip_filter, IPFilter)
        assert len(ip_filter._allowed_ips) == 5880
        assert '79.142.16.1' in ip_filter
        assert '195.189.100.19' in ip_filter
