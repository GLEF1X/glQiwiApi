import abc


class AbstractPaymentWrapper(abc.ABC):
    @abc.abstractmethod
    async def get_balance(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def _auth_token(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def to_card(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def to_wallet(self, *args, **kwargs) -> None:
        raise NotImplementedError()
