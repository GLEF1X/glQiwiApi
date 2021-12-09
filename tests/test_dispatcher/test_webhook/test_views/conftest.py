from typing import no_type_check

import pytest


@no_type_check
@pytest.fixture
def loop(event_loop):
    """
    Spike for compatibility pytest-asyncio and pytest-aiohttp
    @param event_loop:
    @return:
    """
    return event_loop
