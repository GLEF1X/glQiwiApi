from __future__ import annotations

import abc
import typing as t

from glQiwiApi.plugins.abc import Pluggable

if t.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher


class TelegramPlugin(Pluggable, abc.ABC):
    def __init__(self, dispatcher: Dispatcher) -> None:
        self.bot = dispatcher.bot
        self.dispatcher = dispatcher
