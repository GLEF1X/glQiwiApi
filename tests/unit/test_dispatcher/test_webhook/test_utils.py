from aiohttp import web
from aiohttp.web_request import Request

from glQiwiApi.core.dispatcher.webhooks.utils import inject_dependencies


class A:
    pass


class B:
    pass


class SomeView(web.View):
    def __init__(self, request: Request, a: A, b: B):
        super().__init__(request)
        self.a = a
        self.b = b

    async def post(self):
        return web.json_response(data={"ok": True})


def test_inject_dependencies():
    dependencies = {"a": A(), "b": B()}
    patched_view = inject_dependencies(SomeView, dependencies)
    assert patched_view("hello").a == dependencies["a"]  # type: ignore  # noqa
    assert patched_view("hello").b == dependencies["b"]  # type: ignore  # noqa
