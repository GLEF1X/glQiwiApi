from glQiwiApi.core import Wrapper, RequestService


class _SomeWrapper(Wrapper):

    def __init__(self, request_service: RequestService):
        self._request_service = request_service

    def get_request_service(self) -> RequestService:
        return self._request_service


def test_enable_caching():
    request_service = RequestService(cache_time=0)
    wrapper = _SomeWrapper(request_service)
    wrapper.enable_caching(cache_time_in_seconds=5)
    assert request_service._cache._invalidate_strategy.is_cache_disabled is False
    assert request_service._cache._invalidate_strategy._cache_time == 5


def test_disable_caching():
    request_service = RequestService(cache_time=5)
    wrapper = _SomeWrapper(request_service)
    wrapper.disable_caching()
    assert request_service._cache._invalidate_strategy.is_cache_disabled is True
