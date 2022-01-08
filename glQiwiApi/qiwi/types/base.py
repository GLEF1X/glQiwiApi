from __future__ import annotations

from typing import TYPE_CHECKING

from glQiwiApi.base_types.base import BaseWithClient, HashableBaseWithClient

if TYPE_CHECKING:
    from glQiwiApi import QiwiWallet, QiwiP2PClient  # noqa


class QiwiWalletResultBaseWithClient(BaseWithClient["QiwiWallet"]):
    pass


class QiwiWalletResultHashableBaseWithClient(HashableBaseWithClient["QiwiWallet"]):
    pass


class P2PBase(HashableBaseWithClient["QiwiP2PClient"]):
    pass
